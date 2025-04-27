import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCircleCheck } from '@fortawesome/free-solid-svg-icons'

export default function ExperimentPage(props) {
  const { id } = useParams();
  const [experiment, setExperiment] = useState([])

  useEffect(() => {
    fetch(`http://localhost:8008/experiment/${id}`)
      .then(res => res.json())
      .then(json => { setExperiment(json) })
      .catch(err => { console.error(err) })
  }, [])

  return (
    <div className='page'>
      <h2> Experiment {id} </h2>
      <table className="result-table">
        <tbody>
          <tr>
            <th> start date</th>
            <td> {experiment.start_date?.split('T')[0]} </td>
          </tr>
          <tr>
            <th> dispense ligands</th>
            <td> {experiment.dispense_ligands} </td>
          </tr>
          <tr>
            <th> dispense assay mix</th>
            <td> {experiment.dispense_assay_mix} </td>
          </tr>
          <tr>
            <th> centrifuge rpm</th>
            <td> {experiment.centrifuge_rpm} </td>
          </tr>
          <tr>
            <th> centrifuge minutes</th>
            <td> {experiment.centrifuge_minutes} </td>
          </tr>
          <tr>
            <th> protein days thawed</th>
            <td> {experiment.protein_days_thawed} </td>
          </tr>
          <tr>
            <th> Number of Results</th>
            <td> {experiment.results?.length} </td>
          </tr>
          <tr>
            <th> Number of Plates</th>
            <td> {experiment.plates?.length} </td>
          </tr>
        </tbody>
      </table>

      <div className="table-container">
        <table className="result-table">
          <thead>
            <tr>
              <th>Result ID</th>
              <th>V<sub>max</sub></th>
              <th>K<sub>m</sub></th>
              <th>R<sup>2</sup></th>
              <th>Accepted</th>
              <th>Compound</th>
              <th>Protein</th>
            </tr>
          </thead>
          <tbody>
            {
              experiment?.results?.map((result, idx) => <tr key={idx}>
                <td><Link to={`/result/${result.id}`}>Result {result.id}</Link></td>
                <td>{result.vmax ? result.vmax.toFixed(3) : 'N/A'}</td>
                <td>{result.km ? result.km.toFixed(3) : 'N/A'}</td>
                <td>{result.r_squared ? result.r_squared.toFixed(3) : 'N/A'}</td>
                <td>{result.accepted ? <span> <FontAwesomeIcon style={{
                  color: '#72ff72'
                }} icon={faCircleCheck} /> </span> : <></>}</td>
                <td>{result.compound.name}</td>
                <td>{result.protein.name}</td>
              </tr>)
            }
          </tbody>
        </table>
      </div>

    </div>
  )
};

// id
// plates
// results
// binding_experiments
//
// experiment.start_date
// experiment.dispense_assay_mix
// experiment.dispense_ligands
// experiment.centrifuge_minutes
// experiment.centrifuge_rpm
// experiment.protein_days_thawed
//
