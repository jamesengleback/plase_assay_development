import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCircleCheck, faCalendar, faFlask, faVial, faRotate, faVialCircleCheck, faTable } from
  '@fortawesome/free-solid-svg-icons'
import Chip from '../UI/Chip.jsx';

export default function ExperimentCard(props) {
  const { id, num_plates, start_date, dispense_assay_mix, dispense_ligands, centrifuge_minutes, centrifuge_rpm,
    protein_days_thawed, num_results } = props

  return (
    <Link to={`/experiment/${props.id}`} className='experiment-link'>
      <div className='experiment'>
        <div className='row' style={{ justifyContent: 'flex-start', flexWrap: 'wrap' }}>
          <h1> Experiment {props.id} </h1>
          <Chip style={{ backgroundColor: 'var(--gruv-21)' }} label={<span>{dispense_assay_mix}</span>}
            icon={
              <FontAwesomeIcon style={{ color: 'var(--gruv-1)' }} icon={faFlask} />}
          />
          <Chip style={{ backgroundColor: 'var(--gruv-20)' }} label={<span>{dispense_ligands}</span>}
            icon={
              <FontAwesomeIcon style={{ color: 'var(gruv-1)' }} icon={faVial} />}
          />
          <Chip style={{ backgroundColor: 'var(--gruv-28)' }} icon={<FontAwesomeIcon icon={faCalendar} />}
            label={<span>{start_date?.split('T')[0]}</span>}
          />
          <Chip style={{ backgroundColor: 'var(--gruv-25)' }} label={<span>{centrifuge_minutes}m @
            {centrifuge_rpm}rpm</span>}
            icon={
              <FontAwesomeIcon style={{ color: 'var(gruv-1)' }} icon={faRotate} />}
          />
          <Chip style={{ backgroundColor: 'var(--gruv-24)' }} label={<span>{num_results} results</span>}
            icon={
              <FontAwesomeIcon style={{ color: 'var(gruv-1)' }} icon={faVialCircleCheck} />}
          />
          <Chip style={{ backgroundColor: 'var(--gruv-18)' }} label={<span>Plates: {num_plates}</span>}
            icon={
              <FontAwesomeIcon style={{ color: 'var(--gruv-1)' }} icon={faTable} />}
          />
          {protein_days_thawed > 0 && (
            <Chip style={{ backgroundColor: 'var(--gruv-17)' }} label={<span>Thawed: {protein_days_thawed} days</span>}
              icon={
                <FontAwesomeIcon style={{ color: 'var(--gruv-1)' }} icon={faCalendar} />}
            />
          )}
        </div>
      </div>
    </Link>
  )
};

ExperimentCard.propTypes = {
  id: PropTypes.number,
  num_plates: PropTypes.number,
  start_date: PropTypes.string,
  dispense_assay_mix: PropTypes.string,
  dispense_ligands: PropTypes.string,
  centrifuge_minutes: PropTypes.number,
  centrifuge_rpm: PropTypes.number,
  protein_days_thawed: PropTypes.number,
  num_results: PropTypes.number,
};
