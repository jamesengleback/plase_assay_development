import './App.css'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

import ResultListPage from './pages/ResultListPage'
import ResultPage from './pages/ResultPage'
import PlatePage from './pages/PlatePage'
import ExperimentListPage from './pages/ExperimentListPage'
import ExperimentPage from './pages/ExperimentPage'
import Nav from './components/Nav/Nav'

function App() {

  return (
    <Router>
    <Nav routes={[
      { name: 'Experiments', href: '/'},
      { name: 'Plates', href: '/plates'},
      { name: 'Results', href: '/results'},
    ]} />
      <div className='app'>
        <Routes>
          <Route path='/' element={<ExperimentListPage />} />
          <Route path='/experiment' element={<ExperimentListPage />} />
          <Route path='/experiment/:id' element={<ExperimentPage />} />
          <Route path='/plates' element={<PlatePage />} />
          <Route path='/results' element={<ResultListPage />} />
          <Route path='/result/:id' element={<ResultPage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
