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
    <div className='result-nav'>
      <Link to={`/result/${result_id - 1}`}>
        <div className='result-nav-item'>
          <FontAwesomeIcon icon={faChevronLeft} />
        </div >
      </Link>

      <div>
        <span>
          <Link to={`/experiment/${experiment_id}`}>Experiment {experiment_id}</Link> / Result {result_id}
        </span>
    <br/>
        <span> {resultContext.compound?.name} / {resultContext.protein?.name} </span>
      </div>

      <Link to={`/result/${result_id + 1}`}>
        <div className='result-nav-item'>
          <FontAwesomeIcon icon={faChevronRight} />
        </div>
      </Link>
    </div >
  )
};

