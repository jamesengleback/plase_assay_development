import { useState, useEffect } from 'react';
import Plate from '../components/Plate/Plate'

export default function Plates() {
  const [plates, setPlates] = useState([])

  useEffect(() => {
    fetch('http://localhost:8008/plate/')
      .then(res => res.json())
      .then(json => {  setPlates(json) })
      .catch(err => { console.log(err) })
  }, [])
  return (
    <>
      {
        plates.map((item, idx) => <Plate key={`plate-${idx}`} {...item} />)
      }
    </>
  )
}

