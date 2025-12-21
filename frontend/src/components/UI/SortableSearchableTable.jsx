import { useState, useMemo } from 'react';
import PropTypes from 'prop-types';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faAnglesLeft, faAngleLeft, faAngleRight, faAnglesRight } from '@fortawesome/free-solid-svg-icons';

export default function SortableSearchableTable({ data, columns, currentPage, totalPages, onPageChange, limit, onLimitChange, searchTerm, onSearchChange }) {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [hover, setHover] = useState({ first: false, prev: false, next: false, last: false });

  const sortedAndFilteredData = useMemo(() => {
    let filteredData = data;

    if (sortConfig.key) {
      filteredData = [...filteredData].sort((a, b) => {
        const aVal = a[sortConfig.key];
        const bVal = b[sortConfig.key];

        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filteredData;
  }, [data, sortConfig]);

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Search..."
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        style={{ marginBottom: '10px', padding: '5px', width: '100%' }}
      />
      <div className="table-container">
        <table className="result-table">
          <thead>
            <tr>
              {columns.map(col => (
                <th
                  key={col.key}
                  onClick={col.sortable ? () => handleSort(col.key) : undefined}
                  style={{ cursor: col.sortable ? 'pointer' : 'default' }}
                >
                  {col.label}
                  {sortConfig.key === col.key && (
                    <span>{sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedAndFilteredData.map((item, idx) => (
              <tr key={idx}>
                {columns.map(col => (
                  <td key={col.key}>
                    {col.render ? col.render(item) : item[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div style={{ marginTop: '10px', textAlign: 'center' }}>
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '10px' }}>
            <div>
              <label>Page Size: </label>
              <select value={limit} onChange={(e) => onLimitChange(Number(e.target.value))}>
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>
            <div>
              Page {currentPage} of {totalPages}
            </div>
          </div>
          <div style={{ marginTop: '10px' }}>
            <button 
              onClick={() => onPageChange(1)} 
              disabled={currentPage === 1}
              onMouseEnter={() => setHover(prev => ({ ...prev, first: true }))}
              onMouseLeave={() => setHover(prev => ({ ...prev, first: false }))}
              style={{ 
                backgroundColor: currentPage === 1 ? 'lightgrey' : hover.first ? 'var(--gruv-22)' : undefined,
                color: currentPage === 1 ? 'grey' : undefined
              }}
            >
              <FontAwesomeIcon icon={faAnglesLeft} /> First
            </button>
            <button 
              onClick={() => onPageChange(currentPage - 1)} 
              disabled={currentPage === 1}
              onMouseEnter={() => setHover(prev => ({ ...prev, prev: true }))}
              onMouseLeave={() => setHover(prev => ({ ...prev, prev: false }))}
              style={{ 
                backgroundColor: currentPage === 1 ? 'lightgrey' : hover.prev ? 'var(--gruv-22)' : undefined,
                color: currentPage === 1 ? 'grey' : undefined
              }}
            >
              <FontAwesomeIcon icon={faAngleLeft} /> Previous
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button
                key={page}
                onClick={() => onPageChange(page)}
                style={{ margin: '0 5px', fontWeight: page === currentPage ? 'bold' : 'normal' }}
              >
                {page}
              </button>
            ))}
            <button 
              onClick={() => onPageChange(currentPage + 1)} 
              disabled={currentPage === totalPages}
              onMouseEnter={() => setHover(prev => ({ ...prev, next: true }))}
              onMouseLeave={() => setHover(prev => ({ ...prev, next: false }))}
              style={{ 
                backgroundColor: currentPage === totalPages ? 'lightgrey' : hover.next ? 'var(--gruv-22)' : undefined,
                color: currentPage === totalPages ? 'grey' : undefined
              }}
            >
              Next <FontAwesomeIcon icon={faAngleRight} />
            </button>
            <button 
              onClick={() => onPageChange(totalPages)} 
              disabled={currentPage === totalPages}
              onMouseEnter={() => setHover(prev => ({ ...prev, last: true }))}
              onMouseLeave={() => setHover(prev => ({ ...prev, last: false }))}
              style={{ 
                backgroundColor: currentPage === totalPages ? 'lightgrey' : hover.last ? 'var(--gruv-22)' : undefined,
                color: currentPage === totalPages ? 'grey' : undefined
              }}
            >
              Last <FontAwesomeIcon icon={faAnglesRight} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

SortableSearchableTable.propTypes = {
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
  columns: PropTypes.arrayOf(PropTypes.shape({
    key: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,
    sortable: PropTypes.bool,
    render: PropTypes.func
  })).isRequired,
  currentPage: PropTypes.number,
  totalPages: PropTypes.number,
  onPageChange: PropTypes.func,
  limit: PropTypes.number,
  onLimitChange: PropTypes.func,
  searchTerm: PropTypes.string,
  onSearchChange: PropTypes.func
};