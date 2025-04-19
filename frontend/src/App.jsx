import { useState, useEffect } from 'react';
import './App.css'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

import Result from './components/Result'
import Experiment from './components/Experiment/Experiment'
import Plate from './components/Plate/Plate'

function ExperimentList() {
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
          <Experiment key={idx} {...item} />
        </>
        )
        )
      }
    </>
  )
}

function Plates() {
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

function App() {

  return (
    <Router>
      <nav>
        <ul>
          <li><a href='/'>home</a></li>
        </ul>
        <ul>
          <li><a href='/plates'>plates</a></li>
        </ul>
      </nav>
      <div className='app'>
        <Routes>
          <Route path='/' element={<ExperimentList />} />
          <Route path='/plates' element={<Plates />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
