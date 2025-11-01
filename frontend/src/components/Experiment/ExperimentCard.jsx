import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCircleCheck, faCalendar, faFlask, faVial, faRotate, faVialCircleCheck } from
  '@fortawesome/free-solid-svg-icons'
import Chip from '../UI/Chip.jsx';

export default function ExperimentCard(props) {
  const { id, plates, start_date, dispense_assay_mix, dispense_ligands, centrifuge_minutes, centrifuge_rpm,
    protein_days_thawed, results } = props
  const params = [
    //'id',
    //'plates',
    'start_date',
    'dispense_assay_mix',
    'dispense_ligands',
    'centrifuge_minutes',
    'centrifuge_rpm',
    'protein_days_thawed',
  ]

  return (
    <div className='experiment'>
      <div className='row' style={{ justifyContent: 'space-between' }}>
        <Link to={`/experiment/${props.id}`}>
          <h1> Experiment {props.id} </h1>
        </Link>
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
        <Chip style={{ backgroundColor: 'var(--gruv-24)' }} label={<span>{results?.length} results</span>}
          icon={
            <FontAwesomeIcon style={{ color: 'var(gruv-1)' }} icon={faVialCircleCheck} />}
        />
      </div>
    </div>
  )
};

ExperimentCard.propTypes = {
  id: PropTypes.number,
  plates: PropTypes.arrayOf(PropTypes.number),
  start_date: PropTypes.instanceOf(Date),
  dispense_assay_mix: PropTypes.string,
  dispense_ligands: PropTypes.string,
  centrifuge_minutes: PropTypes.number,
  centrifuge_rpm: PropTypes.number,
  protein_days_thawed: PropTypes.number,
};
