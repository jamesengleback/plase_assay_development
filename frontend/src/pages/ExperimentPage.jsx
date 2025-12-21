import { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import Chip from '../components/UI/Chip.jsx';
import SortableSearchableTable from '../components/UI/SortableSearchableTable.jsx';
import { faCircleCheck, faCalendar, faFlask, faVial, faRotate, faVialCircleCheck, faTable } from
  '@fortawesome/free-solid-svg-icons'

export default function ExperimentPage() {
  const { id } = useParams();
  const [experiment, setExperiment] = useState({})
  const [allResults, setAllResults] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [limit, setLimit] = useState(10)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetch(`http://localhost:8008/experiment/${id}`)
      .then(res => res.json())
      .then(json => { setExperiment(json) })
      .catch(err => { console.error(err) })
  }, [id])

  useEffect(() => {
    const url = `http://localhost:8008/result/?experiment_id=${id}${searchTerm ? `&search=${encodeURIComponent(searchTerm)}` : ''}`
    fetch(url)
      .then(res => res.json())
      .then(json => { 
        setAllResults(json)
        setTotal(json.length)
        setTotalPages(Math.ceil(json.length / limit))
      })
      .catch(err => { console.error(err) })
  }, [id, limit, searchTerm])

  const results = useMemo(() => {
    return allResults.slice((currentPage - 1) * limit, currentPage * limit)
  }, [allResults, currentPage, limit])

  const handlePageChange = (page) => {
    setCurrentPage(page)
  }

  const handleLimitChange = (newLimit) => {
    setLimit(newLimit)
    setCurrentPage(1) // Reset to first page
  }

  const columns = [
    {
      key: 'id',
      label: 'Result ID',
      sortable: true,
      render: (result) => <Link to={`/result/${result.id}`}>Result {result.id}</Link>
    },
    {
      key: 'vmax',
      label: 'Vmax',
      sortable: true,
      render: (result) => {
        const vmax = typeof result.vmax === 'object' ? result.vmax.parsedValue : result.vmax;
        return vmax ? vmax.toFixed(3) : 'N/A';
      }
    },
    {
      key: 'km',
      label: 'Km',
      sortable: true,
      render: (result) => {
        const km = typeof result.km === 'object' ? result.km.parsedValue : result.km;
        return km ? km.toFixed(3) : 'N/A';
      }
    },
    {
      key: 'r_squared',
      label: 'R²',
      sortable: true,
      render: (result) => {
        const r_squared = typeof result.r_squared === 'object' ? result.r_squared.parsedValue : result.r_squared;
        return r_squared ? r_squared.toFixed(3) : 'N/A';
      }
    },
    {
      key: 'locked',
      label: 'Locked',
      sortable: true,
      render: (result) => result.locked ? <FontAwesomeIcon style={{ color: '#72ff72' }} icon={faCircleCheck} /> : null
    },
    {
      key: 'accepted',
      label: 'Accepted',
      sortable: true,
      render: (result) => result.accepted ? <FontAwesomeIcon style={{ color: '#72ff72' }} icon={faCircleCheck} /> : null
    },
    {
      key: 'compound',
      label: 'Compound',
      sortable: false,
      render: (result) => result.compound?.name
    },
    {
      key: 'protein',
      label: 'Protein',
      sortable: false,
      render: (result) => result.protein?.name
    },
    {
      key: 'well_volume',
      label: 'Well Volume',
      sortable: true,
      render: (result) => result.well_volume
    },
    {
      key: 'protein_concentration',
      label: '[Protein]',
      sortable: true,
      render: (result) => result.protein_concentration
    },
    {
      key: 'annotations',
      label: 'Annotations',
      sortable: false,
      render: (result) => result.annotations?.map(i => i.comment).join(' / ')
    }
  ];

  return (
    <div className='page'>
      <h2> Experiment {id} </h2>
      <div style={{ width: 'fit-content' }}>
        <div className='row' style={{ justifyContent: 'space-between', width: '100%' }}>
          <Chip style={{ backgroundColor: 'var(--gruv-24)' }} label={<span>{total}{' '}
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

        <SortableSearchableTable 
          data={results} 
          columns={columns} 
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={handlePageChange}
          limit={limit}
          onLimitChange={handleLimitChange}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
        />

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
