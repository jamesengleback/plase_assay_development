import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';

export default function ExperimentCard(props) {
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
    <div className='experiment' >
      <Link to={`/experiment/${props.id}`}>
        <h1> Experiment {props.id} </h1>
      </Link>
      <table>
        <tbody>
          {
            params.map((item, idx) => (
              <tr key={idx} index={idx}>
                <th> {item} </th>
                <td> {props[item] || ''} </td>
              </tr>
            ))
          }
        </tbody>
      </table>
    </div >
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
