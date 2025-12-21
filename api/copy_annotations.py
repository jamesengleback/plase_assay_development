#!/usr/bin/env python3
"""
Script to copy annotations from a database backup to the current database.
Copies result.locked, result.accepted, dose_response.exclude, result comments, and well.exclude.
"""

import sys
import os
from sqlmodel import SQLModel, Session, select, create_engine, text, and_
import logging

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

import api.model as model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_backup_engine(backup_db_path):
    """Create engine for the backup database."""
    backup_url = f"sqlite:///{backup_db_path}"
    return create_engine(backup_url, echo=False)

def clear_existing_annotations(new_session):
    """Clear all existing annotations in the current database."""
    logger.info("Clearing existing annotations...")

    # Clear result annotations
    new_session.exec(text("UPDATE result SET locked = 0, accepted = 0"))
    new_session.exec(text("DELETE FROM resultannotation"))

    # Clear dose_response exclusions (if table exists)
    try:
        new_session.exec(text("UPDATE doseresponse SET exclude = 0"))
    except Exception:
        logger.info("dose_response table not found in current database, skipping...")

    # Clear well exclusions
    try:
        new_session.exec(text("DELETE FROM wellannotation WHERE exclude = 1"))
    except Exception:
        logger.info("wellannotation table not found in current database, skipping...")

    new_session.commit()
    logger.info("Existing annotations cleared")

def copy_result_annotations(backup_session, new_session):
    """Copy result annotations from backup to new database."""
    logger.info("Copying result annotations...")

    # Use raw SQL to avoid schema mismatch issues
    backup_conn = backup_session.connection()
    
    # Get results with annotations, including well and file information for better matching
    result = backup_conn.execute(text("""
        SELECT r.id, r.experiment_id, r.compound_id, r.protein_id, r.locked, r.accepted,
               r.plate_id, r.plate_data_file_id, r.km, r.vmax, r.r_squared,
               c.name as compound_name, pr.name as protein_name, r.protein_concentration as protein_concentration,
               pl.label as plate_label, pl.product_name as plate_product_name,
               pdf.path as plate_file_path,
               w.address as well_address,
               e.dispense_assay_mix, e.dispense_ligands,
               wrl.well_type, w.compound_concentration, w.volume
        FROM result r
        LEFT JOIN compound c ON r.compound_id = c.id
        LEFT JOIN protein pr ON r.protein_id = pr.id
        LEFT JOIN experiment e ON r.experiment_id = e.id
        LEFT JOIN plate pl ON r.plate_id = pl.id
        LEFT JOIN platedatafile pdf ON r.plate_data_file_id = pdf.id
        LEFT JOIN wellresultlink wrl ON r.id = wrl.result_id
        LEFT JOIN well w ON wrl.well_id = w.id
        WHERE r.locked = 1 OR r.accepted = 1 OR EXISTS (
            SELECT 1 FROM resultannotation ra WHERE ra.result_id = r.id
        )
    """))
    
    updated_count = 0
    
    for row in result:
        (result_id, experiment_id, compound_id, protein_id, locked, accepted,
         plate_id, plate_data_file_id, km, vmax, r_squared,
         compound_name, protein_name, protein_concentration,
         plate_label, plate_product_name,
         plate_file_path, well_address, dispense_assay_mix, dispense_ligands,
         well_type, well_compound_concentration, well_volume) = row
        
        # Build matching query with simplified criteria
        query = select(model.Result).where(
            model.Result.experiment_id == experiment_id
        )
        
        # Add compound matching
        if compound_name:
            query = query.where(model.Result.compound.has(name=compound_name))
        else:
            query = query.where(model.Result.compound_id.is_(None))
        
        # Add protein matching
        if protein_name:
            query = query.where(model.Result.protein.has(name=protein_name))
        else:
            query = query.where(model.Result.protein_id.is_(None))
        
        if protein_concentration is not None:
            query = query.where(model.Result.protein_concentration == protein_concentration)
        
        # Add plate matching by file path
        if plate_file_path:
            query = query.where(model.Result.plate_data_file_id.in_(
                select(model.PlateDataFile.id).where(model.PlateDataFile.path == plate_file_path)
            ))
        
        # Add plate_id matching for uniqueness
        if plate_id is not None:
            query = query.where(model.Result.plate_id == plate_id)
        
        # Add well matching
        if well_address:
            query = query.where(model.Result.wells.any(model.Well.address == well_address))
        
        # Add experiment dispense fields
        if dispense_assay_mix is not None:
            query = query.where(model.Result.experiment.has(dispense_assay_mix=dispense_assay_mix))
        if dispense_ligands is not None:
            query = query.where(model.Result.experiment.has(dispense_ligands=dispense_ligands))
        
        # Add plate label and product_name
        if plate_label is not None:
            query = query.where(model.Result.plate.has(label=plate_label))
        if plate_product_name is not None:
            query = query.where(model.Result.plate.has(product_name=plate_product_name))
        
        # Add well type, compound_concentration, volume
        # if well_type is not None:
        #     query = query.where(model.Result.wells.any(model.Well.well_type == well_type))
        if well_compound_concentration is not None:
            query = query.where(model.Result.wells.any(model.Well.compound_concentration == well_compound_concentration))
        if well_volume is not None:
            query = query.where(model.Result.wells.any(model.Well.volume == well_volume))
        
        matching_results = new_session.exec(query).all()

        if len(matching_results) == 1:
            new_result = matching_results[0]

            # Copy locked and accepted
            if locked:
                new_result.locked = True
            if accepted:
                new_result.accepted = True

            # Copy comments - get them from backup
            comments_result = backup_conn.execute(text("""
                SELECT comment FROM resultannotation WHERE result_id = :result_id
            """), {"result_id": result_id})
            
            for comment_row in comments_result:
                comment = comment_row[0]
                # Check if comment already exists
                existing = new_session.exec(
                    select(model.ResultAnnotation).where(
                        model.ResultAnnotation.result_id == new_result.id,
                        model.ResultAnnotation.comment == comment
                    )
                ).first()

                if not existing:
                    new_annotation = model.ResultAnnotation(
                        result_id=new_result.id,
                        comment=comment
                    )
                    new_session.add(new_annotation)

            new_session.add(new_result)
            updated_count += 1
            logger.debug(f"Updated result {new_result.id} for experiment {experiment_id}, compound {compound_name}, well {well_address}")

        elif len(matching_results) > 1:
            logger.warning(f"Multiple matches found for result in experiment {experiment_id}, compound {compound_name}, well {well_address}, file {plate_file_path}")
        else:
            logger.warning(f"No match found for result in experiment {experiment_id}, compound {compound_name}, well {well_address}, file {plate_file_path}")

    new_session.commit()
    logger.info(f"Updated {updated_count} results")

def copy_dose_response_annotations(backup_session, new_session):
    """Copy dose_response.exclude from backup to new database."""
    logger.info("Copying dose response annotations...")

    backup_conn = backup_session.connection()
    
    # Check if dose_response table exists in backup
    table_check = backup_conn.execute(text("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='doseresponse'
    """)).fetchone()
    
    if not table_check:
        logger.info("dose_response table not found in backup database, skipping...")
        return
    
    # Get excluded dose responses with result info, including well and file information
    result = backup_conn.execute(text("""
        SELECT dr.result_id, dr.concentration, dr.exclude,
               r.experiment_id, r.plate_id, r.plate_data_file_id, r.km, r.vmax,
               c.name as compound_name, p.name as protein_name, r.protein_concentration as protein_concentration,
               pl.label as plate_label, pl.product_name as plate_product_name,
               pdf.path as plate_file_path,
               w.address as well_address,
               e.dispense_assay_mix, e.dispense_ligands,
               wrl.well_type, w.compound_concentration, w.volume
        FROM doseresponse dr
        JOIN result r ON dr.result_id = r.id
        LEFT JOIN experiment e ON r.experiment_id = e.id
        LEFT JOIN compound c ON r.compound_id = c.id
        LEFT JOIN protein p ON r.protein_id = p.id
        LEFT JOIN plate pl ON r.plate_id = pl.id
        LEFT JOIN platedatafile pdf ON r.plate_data_file_id = pdf.id
        LEFT JOIN wellresultlink wrl ON r.id = wrl.result_id
        LEFT JOIN well w ON wrl.well_id = w.id
        WHERE dr.exclude = 1
    """))
    
    updated_count = 0

    for row in result:
        (result_id, concentration, exclude, experiment_id, plate_id, plate_data_file_id, km, vmax,
         compound_name, protein_name, protein_concentration,
         plate_label, plate_product_name,
         plate_file_path, well_address, dispense_assay_mix, dispense_ligands,
         well_type, well_compound_concentration, well_volume) = row

        # Build matching query with simplified criteria
        query = select(model.Result).where(
            model.Result.experiment_id == experiment_id
        )
        
        # Add compound matching
        if compound_name:
            query = query.where(model.Result.compound.has(name=compound_name))
        else:
            query = query.where(model.Result.compound_id.is_(None))
        
        # Add protein matching
        if protein_name:
            query = query.where(model.Result.protein.has(name=protein_name))
        else:
            query = query.where(model.Result.protein_id.is_(None))
        
        if protein_concentration is not None:
            query = query.where(model.Result.protein_concentration == protein_concentration)
        
        # Add plate matching by file path
        if plate_file_path:
            query = query.where(model.Result.plate_data_file_id.in_(
                select(model.PlateDataFile.id).where(model.PlateDataFile.path == plate_file_path)
            ))
        
        # Add plate_id matching for uniqueness
        if plate_id is not None:
            query = query.where(model.Result.plate_id == plate_id)
        
        # Add well matching
        if well_address:
            query = query.where(model.Result.wells.any(model.Well.address == well_address))
        
        # Add experiment dispense fields
        if dispense_assay_mix is not None:
            query = query.where(model.Result.experiment.has(dispense_assay_mix=dispense_assay_mix))
        if dispense_ligands is not None:
            query = query.where(model.Result.experiment.has(dispense_ligands=dispense_ligands))
        
        # Add plate label and product_name
        if plate_label is not None:
            query = query.where(model.Result.plate.has(label=plate_label))
        if plate_product_name is not None:
            query = query.where(model.Result.plate.has(product_name=plate_product_name))
        
        # Add well type, compound_concentration, volume
        # if well_type is not None:
        #     query = query.where(model.Result.wells.any(model.Well.well_type == well_type))
        if well_compound_concentration is not None:
            query = query.where(model.Result.wells.any(model.Well.compound_concentration == well_compound_concentration))
        if well_volume is not None:
            query = query.where(model.Result.wells.any(model.Well.volume == well_volume))
        
        matching_results = new_session.exec(query).all()

        if len(matching_results) == 1:
            new_result = matching_results[0]

            # Find matching dose response by concentration
            matching_dr = new_session.exec(
                select(model.DoseResponse).where(
                    model.DoseResponse.result_id == new_result.id,
                    model.DoseResponse.concentration == concentration
                )
            ).first()

            if matching_dr:
                matching_dr.exclude = True
                new_session.add(matching_dr)
                updated_count += 1
                logger.debug(f"Excluded dose response for result {new_result.id}, concentration {concentration}")
            else:
                logger.warning(f"No matching dose response found for result {new_result.id}, concentration {concentration}")

    new_session.commit()
    logger.info(f"Updated {updated_count} dose responses")

def copy_well_annotations(backup_session, new_session):
    """Copy well.exclude from backup to new database."""
    logger.info("Copying well annotations...")

    backup_conn = backup_session.connection()
    
    # Check if wellannotation table exists in backup
    table_check = backup_conn.execute(text("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='wellannotation'
    """)).fetchone()
    
    if not table_check:
        logger.info("wellannotation table not found in backup database, skipping...")
        return
    
    # Get excluded well annotations with well info
    result = backup_conn.execute(text("""
        SELECT wa.well_id, wa.exclude, wa.comment,
               w.address, w.plate_id, p.experiment_id, p.label, p.product_name,
               pdf.path as plate_file_path
        FROM wellannotation wa
        JOIN well w ON wa.well_id = w.id
        JOIN plate p ON w.plate_id = p.id
        LEFT JOIN platedatafile pdf ON p.plate_data_file_id = pdf.id
        WHERE wa.exclude = 1
    """))
    
    updated_count = 0

    for row in result:
        well_id, exclude, comment, address, plate_id, experiment_id, plate_label, plate_product_name, plate_file_path = row

        # Find matching well by experiment, plate file path, and address
        query = select(model.Well).where(
            model.Well.plate.has(model.Plate.experiment_id == experiment_id)
        )
        
        # Add plate file path matching
        if plate_file_path:
            query = query.where(model.Well.plate.has(
                model.Plate.plate_data_file_id.in_(
                    select(model.PlateDataFile.id).where(model.PlateDataFile.path == plate_file_path)
                )
            ))
        
        # Add plate_id matching for uniqueness
        if plate_id is not None:
            query = query.where(model.Well.plate_id == plate_id)
        
        query = query.where(model.Well.address == address)
        
        matching_wells = new_session.exec(query).all()

        if len(matching_wells) == 1:
            new_well = matching_wells[0]

            # Check if annotation already exists
            existing = new_session.exec(
                select(model.WellAnnotation).where(
                    model.WellAnnotation.well_id == new_well.id,
                    model.WellAnnotation.exclude == True
                )
            ).first()

            if not existing:
                new_annotation = model.WellAnnotation(
                    well_id=new_well.id,
                    exclude=True,
                    comment=comment  # Also copy comment if present
                )
                new_session.add(new_annotation)
                updated_count += 1
                logger.debug(f"Excluded well {address} in experiment {experiment_id}")
        elif len(matching_wells) > 1:
            logger.warning(f"Multiple matches found for well {address} in experiment {experiment_id}")
        else:
            logger.warning(f"No match found for well {address} in experiment {experiment_id}")

    new_session.commit()
    logger.info(f"Updated {updated_count} wells")

def main():
    if len(sys.argv) != 2:
        print("Usage: python copy_annotations.py <backup_database_path>")
        sys.exit(1)

    backup_db_path = sys.argv[1]

    if not os.path.exists(backup_db_path):
        print(f"Backup database not found: {backup_db_path}")
        sys.exit(1)

    # Create engines
    backup_engine = create_backup_engine(backup_db_path)
    new_engine = model.engine  # Current database

    # Create sessions
    with Session(backup_engine) as backup_session, Session(new_engine) as new_session:
        try:
            clear_existing_annotations(new_session)
            copy_result_annotations(backup_session, new_session)
            copy_dose_response_annotations(backup_session, new_session)
            copy_well_annotations(backup_session, new_session)
            logger.info("Annotation copying completed successfully")
        except Exception as e:
            logger.error(f"Error during annotation copying: {e}")
            new_session.rollback()
            raise

if __name__ == "__main__":
    main()