import { useEffect, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faChevronRight,
  faChevronLeft,
} from '@fortawesome/free-solid-svg-icons'
import { ResultContext } from './ResultContext';

export default function ResultNavigation(props) {
  const navigate = useNavigate()
  const resultContext = useContext(ResultContext);
  const result_id = resultContext.id
  const experiment_id = resultContext.experiment_id

  useEffect(() => {
    const handleKeyDown = (event) => {
      switch (event.key) {
        case 'ArrowLeft':
          event.preventDefault();
          navigate(`/result/${result_id - 1}`);
          break;
        case 'ArrowRight':
          event.preventDefault();
          navigate(`/result/${result_id + 1}`);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [navigate, result_id]);

  return (
    <div className='result-nav' style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center', 
      width: '100%', 
      padding: '1em', 
      backgroundColor: 'var(--bg-dark)', 
      borderRadius: '5px', 
      marginBottom: '1em' 
    }}>
      <Link to={`/result/${result_id - 1}`} style={{ textDecoration: 'none' }}>
        <button className="nav-button">
          <FontAwesomeIcon icon={faChevronLeft} /> Previous
        </button>
      </Link>

      <div style={{ textAlign: 'center' }}>
        <span>
          <Link to={`/experiment/${experiment_id}`} style={{ color: 'var(--fg)', textDecoration: 'none' }}>Experiment {experiment_id}</Link> / Result {result_id}
        </span>
        <br/>
        <span> {resultContext.compound?.name} / {resultContext.protein?.name} </span>
      </div>

      <Link to={`/result/${result_id + 1}`} style={{ textDecoration: 'none' }}>
        <button className="nav-button">
          Next <FontAwesomeIcon icon={faChevronRight} />
        </button>
      </Link>
      <style>{`
        .nav-button {
          padding: 0.5em 1em;
          background-color: var(--gruv-5);
          color: var(--fg);
          border: none;
          border-radius: 5px;
          cursor: pointer;
        }
        .nav-button:hover {
          background-color: var(--gruv-28);
        }
      `}</style>
    </div >
  )
};

