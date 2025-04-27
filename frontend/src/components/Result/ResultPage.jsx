import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import PropTypes from 'prop-types';
import Result, { ResultTable } from './Result';
import ResultResponseTable from './ResultResponseTable';
import AbsorbancePlotMultiple from '../Absorbance/AbsorbancePlotMultiple';
import { Link } from 'react-router-dom';
import Compound from '../Compound/Compound';
import Protein from '../Protein/Protein';
import ResponsePlot from './ResponsePlot';
import Spinner from '../utils/Spinner/Spinner';

import './Result.css'

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faChevronRight, faChevronLeft, faDeleteLeft } from '@fortawesome/free-solid-svg-icons'


function ResultNavigation(props) {
  const id = props.id
  const experiment_id = props.experiment_id
  return (
    <div className='result-nav'>
      <div className='result-nav-item'>
        <Link to={`/result/${id - 1}`}>
          <FontAwesomeIcon icon={faChevronLeft} />
        </Link>
      </div >

      <div>
        <span>
          <Link to={`/experiment/${experiment_id}`}> Experiment {experiment_id} </Link>
          /
          <Link to={`/result/${id}`}> Result {id} </Link>
        </span>
      </div>

      <Link to={`/result/${id + 1}`}>
        <div className='result-nav-item'>
          <FontAwesomeIcon icon={faChevronRight} />
        </div>
      </Link>
    </div >
  )
};

function ResultAnnotate(props) {
  const id = props.id // result id
  const setResult = props.setResult
  const [accept, setAccept] = useState(props.accepted)
  const [comments, setComments] = useState([])
  const [commentInput, setCommentInput] = useState([])

  useEffect(() => {
    if (id) {
      fetch(`http://localhost:8008/comment/?result_id=${id}`)
        .then(res => res.json())
        .then(json => { setComments(json); })
        .catch(err => { console.error(err) })
    }
  }, [id])

  return (
    <div className='info-card comment-container'>
      <div>
        <label for='accept-checkbox'> Accept </label>
        <input id='accept-checkbox'
          type='checkbox'
          checked={props.accepted}
          onChange={(event) => {
            const checked = event.target.checked
            const form = new FormData()
            form.append('accept', checked)
            fetch(`http://localhost:8008/result/${id}`,
              {
                method: 'PATCH',
                body: form
              }
            )
              .then(res => {
                setAccept(checked)
              })
              .catch(err => { console.error(err) })
          }}
        />
      </div>
      <form action={() => {
        const form = new FormData()
        form.append('result_id', id)
        form.append('comment', commentInput)
        fetch(`http://localhost:8008/comment/`,
          {
            method: 'POST',
            body: form
          }
        )
          .then(res => res.json())
          .then(json => {
            console.warn(json)
            setComments([json, ...comments])
          })
          .catch(err => { console.error(err) })
      }}>
        <label for='comment-input'> Comments </label>
        <input id='comment-input'
          name='comment'
          type='text'
          onChange={event => {
            setCommentInput(event.target.value)
          }}
        />
        <button type='submit'>Submit</button>
      </form>
      <div className='comment-list'>
        {
          comments?.map((item, idx) => <div id={`comment-${idx}`} className='comment' key={idx}>
            <span>{item.comment}  </span>
            <button onClick={() => {

              fetch(`http://localhost:8008/comment/${item.id}`,
                { method: 'DELETE' }
              )
                .then(res => {
                  setComments(comments.filter(c => c.id !== item.id))
                  // document.getElementById(`comment-${idx}`).remove() 
                })
                .catch(err => { console.log(err) })
            }}>
              <FontAwesomeIcon icon={faDeleteLeft} />
            </button>
          </div>)
        }
      </div>
    </div >
  )
}

export default function ResultPage(props) {
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState({});
  const [absorbance, setAbsorbance] = useState([]);
  const { id } = useParams();

  useEffect(() => {
    fetch(`http://localhost:8008/result/${id}`)
      .then(res => res.json())
      .then(json => { console.log('result: ', json); return json })
      .then(json => { setResult(json) })
      .then(() => { setLoading(false) })
      .catch(err => { console.log(err) })

  }, [id])

  return <div className='page'>
    <ResultNavigation {...result} />
    {loading ?? <Spinner />}
    <div className='result-container'>
      <div className='main-content'>
        <div className='row'>
          <Compound {...result?.compound} />
          <Protein {...result?.protein} />
          <ResultAnnotate {...result} setResult={setResult} />
        </div>
      </div>
      <div className='main-content'>
        <ResultResponseTable data={result?.dose_response} result_id={result.id} setResult={setResult} />
        <div className='col'>
          <div className='box'>
            <div className='row'>
              <ResponsePlot
                km={result.km}
                vmax={result.vmax}
                dose_response={result.dose_response}
              />
              <ResultTable {...result} />
            </div>
          </div>
          <div className='box'>
            <AbsorbancePlotMultiple data={result.test_wells} />
          </div>
        </div>
      </div>
    </div>
  </div>
}

ResultPage.propTypes = {
  id: PropTypes.number,
}
