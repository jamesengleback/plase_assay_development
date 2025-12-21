from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from ..dependencies import get_session, common_parameters
from ..model import Compound
from .serializers import CompoundVerboseReturnType

from rdkit.Chem import MolFromSmiles
from rdkit.Chem.Descriptors import MolWt

from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem import rdDepictor

router = APIRouter()

def moltosvg(mol, molSize=(450, 150), kekulize=True):
    """from https://rdkit.blogspot.com/2015/02/new-drawing-code.html"""
    mc = Chem.Mol(mol.ToBinary())
    if kekulize:
        try:
            Chem.Kekulize(mc)
        except:
            mc = Chem.Mol(mol.ToBinary())
    if not mc.GetNumConformers():
        rdDepictor.Compute2DCoords(mc)
    drawer = rdMolDraw2D.MolDraw2DSVG(molSize[0], molSize[1])
    drawer.DrawMolecule(mc)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    # It seems that the svg renderer used doesn't quite hit the spec.
    # Here are some fixes to make it work in the notebook, although I think
    # the underlying issue needs to be resolved at the generation step
    return svg.replace("svg:", "")

@router.get("/{id}")
async def get_compound(
    common_parameters: Annotated[dict, Depends(common_parameters)],
    id: int | None = None,
    session: Session = Depends(get_session),
) -> CompoundVerboseReturnType | list[CompoundVerboseReturnType]:

    query = select(Compound)
    if id:
        query = query.where(Compound.id == id)
        data = session.exec(query).first() 

        if not data:
            raise HTTPException(status_code=404, detail=f"Compound with id {id} not found")
        if data.svg is None:
            if data.canonical_smiles is None:
                # Cannot generate SVG without SMILES
                pass
            else:
                try:
                    mol = MolFromSmiles(data.canonical_smiles)
                    if mol is None:
                        raise ValueError("Could not parse SMILES string.")

                    data.svg = moltosvg(mol) 
                    data.mw = MolWt(mol)

                    session.add(data)
                    session.commit()
                    session.refresh(data)

                except Exception as e:
                    print(f"Error processing compound {data.id}: {e}")
                    raise HTTPException(status_code=500, detail="Error generating compound data.")
        
        return data

    query = query.offset(common_parameters["offset"]).limit(common_parameters["limit"])
    data = session.exec(query).all()
    
    return data
