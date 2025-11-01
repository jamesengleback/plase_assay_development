import { useState, useEffect } from 'react';
import './Plate.css';
import PropTypes from 'prop-types';
import Well from './Well.jsx';
import Chip from '../UI/Chip.jsx';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCircleCheck, faCalendar, faFlask, faVial, faRotate, faVialCircleCheck } from
  '@fortawesome/free-solid-svg-icons'

function PlateArray(props) {
  const alphabet = [...'ABCDEFGHIJKLMNOPQRSTUVWXYZ'];
  const nRows = 16
  const nCols = 24

  const [wells, setWells] = useState([])
  const [colorBy, setColorBy] = useState('compound_concentration')

  useEffect(() => {
    fetch(`http://localhost:8008/well/?plate=${props.id}`)
      .then(res => res.json())
      .then(json => Object.fromEntries(json.map(item => [item.address, item])))
      .then(json => { setWells(json) })
      .catch(err => { console.error(err) })
  }, [])
  //const wells = Object.fromEntries(props?.wells.map(item => [item?.address, item]))


  return (
    <div className='plate-array-area'>
      <select onChange={event => { setColorBy(event.target.value) }} value={colorBy} >
        <option value='volume'>Volume</option>
        <option value='compound_concentration'>Compound Concentration</option>
        <option value='protein_concentration'>Protein Concentration</option>
        <option value='total_volume'>Total Volume</option>
        <option value='result_id'>Result Id</option>
      </select>
      <table>
        <tbody>
          {
            [...Array(nRows + 1).keys()].map(rowNo => (
              <tr key={`row-${rowNo}`} className='plate-array-row'>
                {
                  [...Array(nCols + 1).keys()].map(colNo => (
                    (rowNo === 0) ?
                      (colNo !== 0) ?
                        <th key={colNo}>{colNo}</th>
                        :
                        <th key={colNo}></th>
                      :
                      (colNo === 0) ?
                        <th key={`row-${rowNo}-col-${colNo}`}>{alphabet[rowNo - 1]}</th>
                        :
                        <td key={`row-${rowNo}-col-${colNo}`}> <Well color={colorBy} id={props.id} {...wells[`${alphabet[rowNo - 1]}${colNo}`]} /> </td>
                  ))
                }
              </tr>
            )
            )
          }
        </tbody>
      </table>
    </div>
  )
}

export default function Plate(props) {
  const params = [
    'id',
    'plate_data_file_id',
    'plate_data_file',
    'product_name',
    'label',
    'experiment_id',
    'experiment',
  ]
  return (
    <div className='plate'>
      <div className='row'>
        <div className='column'>
          {params.map((item, idx) => <Chip key={idx} style={{ backgroundColor: `var(--gruv-${idx + 15})` }} label={<span>{item} {props[item]}</span>}
            icon={
              <FontAwesomeIcon style={{ color: 'var(--gruv-1)' }} icon={faFlask} />}
          />)
          }
        </div>
        <PlateArray id={props.id} />
      </div>
    </div >
  )
}

// ai slop
//Plate.propTypes = {
//  id: PropTypes.number.isRequired,
//  plate_data_file_id: PropTypes.number,
//  plate_data_file: PropTypes.shape({
//    // Define PropTypes for PlateDataFile if you have its schema
//    id: PropTypes.number.isRequired,
//    // ... other fields of PlateDataFile
//  }),
//  product_name: PropTypes.string,
//  label: PropTypes.string,
//  wells: PropTypes.arrayOf(
//    PropTypes.shape({
//      // Define PropTypes for Well if you have its schema
//      id: PropTypes.number.isRequired,
//      plate_id: PropTypes.number.isRequired,
//      // ... other fields of Well
//    })
//  ).isRequired,
//  experiment_id: PropTypes.number,
//  experiment: PropTypes.shape({
//    // Define PropTypes for Experiment if you have its schema
//    id: PropTypes.number.isRequired,
//    // ... other fields of Experiment
//  }),
//}

const PlatePropTypes = PropTypes.shape({
  id: PropTypes.number.isRequired,
  plate_data_file_id: PropTypes.number,
  plate_data_file: PropTypes.shape({
    // Define PropTypes for PlateDataFile if you have its schema
    id: PropTypes.number.isRequired,
    // ... other fields of PlateDataFile
  }),
  product_name: PropTypes.string,
  label: PropTypes.string,
  wells: PropTypes.arrayOf(
    PropTypes.shape({
      // Define PropTypes for Well if you have its schema
      id: PropTypes.number.isRequired,
      plate_id: PropTypes.number.isRequired,
      // ... other fields of Well
    })
  ).isRequired,
  experiment_id: PropTypes.number,
  experiment: PropTypes.shape({
    // Define PropTypes for Experiment if you have its schema
    id: PropTypes.number.isRequired,
    // ... other fields of Experiment
  }),
});
