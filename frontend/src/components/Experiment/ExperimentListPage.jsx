import PropTypes from 'prop-types';
import { useState, useEffect } from 'react';
import ExperimentCard from './ExperimentCard';

export default function ExperimentListPage() {
  const [experiments, setExperiments] = useState([])

  useEffect(() => {
    fetch('http://localhost:8008/experiment/')
      .then(res => res.json())
      .then(json => { setExperiments(json) })
      .catch(err => { console.log(err) })
  }, [])
  return (
    <>
      {
        experiments.map((item, idx) => (<>
          <ExperimentCard key={idx} {...item} />
        </>
        )
        )
      }
    </>
  )
}

