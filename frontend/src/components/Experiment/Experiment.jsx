import PropTypes from 'prop-types';

export default function Experiment(props) {
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
      <h1> Experiment {props.id} </h1>
      <table>
        <tbody>
          {
            params.map((item, idx) => (
              <tr index={idx}>
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

Experiment.propTypes = {
  id: PropTypes.number,
  plates: PropTypes.arrayOf(PropTypes.number),
  start_date: PropTypes.instanceOf(Date),
  dispense_assay_mix: PropTypes.string,
  dispense_ligands: PropTypes.string,
  centrifuge_minutes: PropTypes.number,
  centrifuge_rpm: PropTypes.number,
  protein_days_thawed: PropTypes.number,
};
