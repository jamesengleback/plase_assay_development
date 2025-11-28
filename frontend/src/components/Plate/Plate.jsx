import { useState, useEffect } from 'react';
import './Plate.css';
import PropTypes from 'prop-types';
import Well from './Well.jsx';
import Chip from '../UI/Chip.jsx';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCircleCheck, faCalendar, faFlask, faVial, faRotate, faVialCircleCheck } from
  '@fortawesome/free-solid-svg-icons'
import infernoScale from '../Absorbance/colors.jsx';


function capitalizeWords(str) {
  if (!str) {
    return str;
  }

  return str.trim().split(/\s+/).map(word => {
    // Handle empty strings that might result from extra spaces
    if (word.length === 0) {
      return '';
    }
    return word.charAt(0).toUpperCase() + word.slice(1);
  }).join(' ');
}


function PlateArray(props) {
  const alphabet = [...'ABCDEFGHIJKLMNOPQRSTUVWXYZ'];
  const nRows = 16
  const nCols = 24

  const [wells, setWells] = useState([])
  const [colorBy, setColorBy] = useState('compound_concentration')
  const [colorScaleNumbers, setColorScaleNumbers] = useState([])
  const [unit, setUnit] = useState('μM')

  useEffect(() => {
    fetch(`http://localhost:8008/well/?plate=${props.id}`)
      .then(res => res.json())
      .then(json => Object.fromEntries(json.map(item => [item.address, item])))
      .then(json => { setWells(json) })
      .catch(err => { console.error(err) })
  }, [])
  //const wells = Object.fromEntries(props?.wells.map(item => [item?.address, item]))

  useEffect(() => {
    console.log('wells: ', wells)
    let colorScaleNumbers
    switch (colorBy) {
      case 'compound_concentration':
        colorScaleNumbers = [...new Set(Object.values(wells).map(item => item?.compound_concentration))].toSorted((a, b) => a > b)
        setColorScaleNumbers(colorScaleNumbers)
        setUnit('μM')
        break;
      case 'protein_concentration':
        colorScaleNumbers = [...new Set(Object.values(wells).map(item => item?.protein_concentration))].toSorted((a, b) => a > b)
        setColorScaleNumbers(colorScaleNumbers)
        setUnit('μM')
        break
    }
  }, [colorBy, props.id])

  return (
    <div className='plate-array-area'>
      <select onChange={event => { setColorBy(event.target.value) }} value={colorBy} >
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
      <div style={{ display: 'flex', flexDirection: 'column', margin: '0.5em' }}>
        <div>{capitalizeWords(colorBy.replace('_', ' '))} ({unit}): </div>
        <div style={{ display: 'flex', flexDirection: 'row', padding: '0.5em' }}>
          {colorScaleNumbers.map((item, idx) => (
            <div key={idx}>
              <div style={{ width: '80px', height: '20px', backgroundColor: infernoScale(item / Math.max(...colorScaleNumbers)) }}></div>
              <div >{item.toFixed(1)}</div>
            </div>
          ))}
        </div>
      </div>
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
