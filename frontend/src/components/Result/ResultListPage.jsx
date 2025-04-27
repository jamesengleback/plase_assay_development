import { useState, useEffect } from 'react';
import Result from './Result';

export default function ResultListPage(props) {
  const [results, setResults] = useState([])
  const [absorbance, setAbsorbance] = useState([])

  useEffect(() => {
    fetch('http://localhost:8008/result/')
      .then(res => res.json())
      .then(json => { setResults(json) })
      .catch(err => { console.log(err) })

  }, [])



  return <>
      {
        results.map((item, idx) => (<>
          <Result key={idx} {...item} />
        </>
        )
        )
      }
  </>
}


