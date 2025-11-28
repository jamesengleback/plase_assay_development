import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import Chip from '../UI/Chip.jsx';
import { faCircleCheck, faCalendar, faFlask, faVial, faRotate, faVialCircleCheck, faTable } from
  '@fortawesome/free-solid-svg-icons'

export default function ExperimentPage(props) {
  const { id } = useParams();
  const [experiment, setExperiment] = useState([])

  useEffect(() => {
    fetch(`http://localhost:8008/experiment/${id}`)
      .then(res => res.json())
      .then(json => { setExperiment(json) })
      .catch(err => { console.error(err) })
  }, [id])

  return (
    <div className='page'>
      <h2> Experiment {id} </h2>
      <div style={{ width: 'fit-content' }}>
        <div className='row' style={{ justifyContent: 'space-between', width: '100%' }}>
          <Chip style={{ backgroundColor: 'var(--gruv-24)' }} label={<span>{experiment.results?.length}{' '}
            results</span>}
            icon={
              <FontAwesomeIcon style={{ color: 'var(gruv-1)' }} icon={faVialCircleCheck} />}
          />
          <Chip style={{ backgroundColor: 'var(--gruv-22)' }} label={<span>{experiment.plates?.length}{' '}
            plates</span>}
            icon={
              <FontAwesomeIcon style={{ color: 'var(gruv-1)' }} icon={faTable} />}
          />
          <vr style={{ width: '1px', backgroundColor: 'var(--fg)', opacity: 0.3 }}></vr>
          <Chip style={{ backgroundColor: 'var(--gruv-21)' }} label={<span>{experiment.dispense_assay_mix}</span>}
            icon={
              <FontAwesomeIcon style={{ color: 'var(--gruv-1)' }} icon={faFlask} />}
          />
          <Chip style={{ backgroundColor: 'var(--gruv-20)' }} label={<span>{experiment.dispense_ligands}</span>}
            icon={
              <FontAwesomeIcon style={{ color: 'var(gruv-1)' }} icon={faVial} />}
          />
          <Chip style={{ backgroundColor: 'var(--gruv-28)' }} icon={<FontAwesomeIcon icon={faCalendar} />}
            label={<span>{experiment.start_date?.split('T')[0]}</span>}
          />
          <Chip style={{ backgroundColor: 'var(--gruv-25)' }} label={<span>{experiment.centrifuge_minutes}m @
            {experiment.centrifuge_rpm}rpm</span>}
            icon={
              <FontAwesomeIcon style={{ color: 'var(gruv-1)' }} icon={faRotate} />}
          />
        </div>

        <div className="table-container">
          <table className="result-table">
            <thead>
              <tr>
                <th>Result ID</th>
                <th>V<sub>max</sub></th>
                <th>K<sub>m</sub></th>
                <th>R<sup>2</sup></th>
                <th>Locked</th>
                <th>Accepted</th>
                <th>Compound</th>
                <th>Protein</th>
                <th>Well Volume</th>
                <th>[Protein]</th>
                <th>Annotations</th>
              </tr>
            </thead>
            <tbody>
              {
                experiment?.results?.map((result, idx) => <tr key={idx}>
                  <td>
                    <Link to={`/result/${result.id}`}>Result {result.id}</Link>
                  </td>
                  <td>{result.vmax ? result.vmax.toFixed(3) : 'N/A'}</td>
                  <td>{result.km ? result.km.toFixed(3) : 'N/A'}</td>
                  <td>{result.r_squared ? result.r_squared.toFixed(3) : 'N/A'}</td>
                  <td>{result.locked ? <span>
                    <FontAwesomeIcon style={{ color: '#72ff72' }} icon={faCircleCheck} />
                  </span> : <></>}</td>
                  <td>{result.accepted ? <span>
                    <FontAwesomeIcon style={{ color: '#72ff72' }} icon={faCircleCheck} />
                  </span> : <></>}</td>
                  <td>{result.compound?.name}</td>
                  <td>{result.protein?.name}</td>
                  <td>{result.well_volume}</td>
                  <td>{result.protein_concentration}</td>
                  <td>{result.annotations.map(i => i.comment).join(' / ')}</td>
                </tr>)
              }
            </tbody>
          </table>
        </div>
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
