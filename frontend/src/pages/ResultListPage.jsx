import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import SortableSearchableTable from '../components/UI/SortableSearchableTable.jsx';
import { faCircleCheck } from '@fortawesome/free-solid-svg-icons'

export default function ResultListPage() {
  const [allResults, setAllResults] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [limit, setLimit] = useState(50)
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState({
    experiment_id: '',
    locked: '',
    accepted: '',
    protein: '',
    well_volume_min: '',
    well_volume_max: '',
    protein_concentration_min: '',
    protein_concentration_max: ''
  })

  useEffect(() => {
    const params = new URLSearchParams();
    if (searchTerm) params.append('search', searchTerm);
    if (filters.experiment_id) params.append('experiment_id', filters.experiment_id);
    if (filters.locked) params.append('locked', filters.locked);
    if (filters.accepted) params.append('accepted', filters.accepted);
    if (filters.protein) params.append('protein', filters.protein);
    if (filters.well_volume_min) params.append('well_volume_min', filters.well_volume_min);
    if (filters.well_volume_max) params.append('well_volume_max', filters.well_volume_max);
    if (filters.protein_concentration_min) params.append('protein_concentration_min', filters.protein_concentration_min);
    if (filters.protein_concentration_max) params.append('protein_concentration_max', filters.protein_concentration_max);
    const url = `http://localhost:8008/result/?${params.toString()}`
    fetch(url)
      .then(res => res.json())
      .then(json => { 
        setAllResults(json)
        setTotal(json.length)
        setTotalPages(Math.ceil(json.length / limit))
      })
      .catch(err => { console.error(err) })
  }, [limit, searchTerm, filters])

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
      key: 'experiment_id',
      label: 'Experiment ID',
      sortable: true,
      render: (result) => <Link to={`/experiment/${result.experiment_id}`}>Exp {result.experiment_id}</Link>
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
      <h2>All Results</h2>
      <div style={{ marginBottom: '1em', display: 'flex', gap: '1em', flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Experiment ID"
          value={filters.experiment_id}
          onChange={(e) => setFilters({ ...filters, experiment_id: e.target.value })}
          style={{ padding: '0.5em' }}
        />
        <select
          value={filters.locked}
          onChange={(e) => setFilters({ ...filters, locked: e.target.value })}
          style={{ padding: '0.5em' }}
        >
          <option value="">All Locked</option>
          <option value="true">Locked</option>
          <option value="false">Unlocked</option>
        </select>
        <select
          value={filters.accepted}
          onChange={(e) => setFilters({ ...filters, accepted: e.target.value })}
          style={{ padding: '0.5em' }}
        >
          <option value="">All Accepted</option>
          <option value="true">Accepted</option>
          <option value="false">Not Accepted</option>
        </select>
        <input
          type="text"
          placeholder="Protein"
          value={filters.protein}
          onChange={(e) => setFilters({ ...filters, protein: e.target.value })}
          style={{ padding: '0.5em' }}
        />
        <div style={{ display: 'flex', gap: '0.5em', alignItems: 'center' }}>
          <label>Well Volume:</label>
          <input
            type="number"
            placeholder="Min"
            value={filters.well_volume_min}
            onChange={(e) => setFilters({ ...filters, well_volume_min: e.target.value })}
            style={{ padding: '0.5em', width: '80px' }}
          />
          <input
            type="number"
            placeholder="Max"
            value={filters.well_volume_max}
            onChange={(e) => setFilters({ ...filters, well_volume_max: e.target.value })}
            style={{ padding: '0.5em', width: '80px' }}
          />
        </div>
        <div style={{ display: 'flex', gap: '0.5em', alignItems: 'center' }}>
          <label>[Protein]:</label>
          <input
            type="number"
            placeholder="Min"
            value={filters.protein_concentration_min}
            onChange={(e) => setFilters({ ...filters, protein_concentration_min: e.target.value })}
            style={{ padding: '0.5em', width: '80px' }}
          />
          <input
            type="number"
            placeholder="Max"
            value={filters.protein_concentration_max}
            onChange={(e) => setFilters({ ...filters, protein_concentration_max: e.target.value })}
            style={{ padding: '0.5em', width: '80px' }}
          />
        </div>
      </div>
      <div style={{ width: 'fit-content' }}>
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
}


