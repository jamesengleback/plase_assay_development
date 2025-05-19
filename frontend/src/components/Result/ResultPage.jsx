import { useState, useEffect, useContext, createContext } from 'react';
import { useParams } from 'react-router-dom';
import PropTypes from 'prop-types';

import Result, { ResultTable } from './Result';
import ResultResponseTable from './ResultResponseTable';
import AbsorbancePlotMultiple from '../Absorbance/AbsorbancePlotMultiple';
import { Link } from 'react-router-dom';
import Compound from '../Compound/Compound';
import Protein from '../Protein/Protein';
import ProteinCard from '../Protein/ProteinCard';
import ResponsePlot from './ResponsePlot';
import Spinner from '../utils/Spinner/Spinner';

import './Result.css'

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faChevronRight,
  faChevronLeft,
  faDeleteLeft,
  faComment,
  faSquareCheck,
  faHourglassStart,
  faLock,
  faLockOpen,
  faCheckCircle,
  faCircleXmark,
} from '@fortawesome/free-solid-svg-icons'

const ResultContext = createContext({})

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
  const [comments, setComments] = useState([])
  const [commentInput, setCommentInput] = useState([])
  const [locked, setLocked] = useState(props.locked)
  const [accepted, setAccepted] = useState(props.accepted)

  const resultContext = useContext(ResultContext);
  const id = resultContext.id // result id

  useEffect(() => {
    if (id) {
      fetch(`http://localhost:8008/comment/?result_id=${id}`)
        .then(res => res.json())
        .then(json => { setComments(json); })
        .catch(err => { console.error(err) })
    }
  }, [id])

  return (
    <div className='info-card'>
      <div className='row comment-submit'>
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
              setComments([json, ...comments]);
              setCommentInput('');
            })
            .catch(err => { console.error(err) })
        }}
          className='comment-submit'
        >
          {/* <label htmlFor='comment-input'> Comments </label> */}
          <input id='comment-input'
            name='comment'
            type='text'
            value={commentInput}
            onChange={event => { setCommentInput(event.target.value) }}
          />
        </form>
        <button
          onClick={(event) => {
            const form = new FormData()
            const val = !locked
            setLocked(val);

            form.append('lock', val)
            fetch(`http://localhost:8008/result/${id}`,
              {
                method: 'PATCH',
                body: form
              }
            )
              .then(res => res.json())
              .then(json => { resultContext.setResult(json) })
              .catch(err => {
                console.error(err);
                setLocked(!locked);
              })
          }}
        >
          {
            (locked) ?
              <FontAwesomeIcon icon={faLockOpen} />
              :
              <FontAwesomeIcon icon={faLock} />
          }
        </button>
        <button
          checked={resultContext.accepted}
          style={{
            backgroundColor: accepted ? 'var(--gruv-5)' : 'var(--gruv-16)'
          }}
          onClick={(event) => {
            const form = new FormData()
            const val = !accepted
            setAccepted(val);
            form.append('accept', val)
            fetch(`http://localhost:8008/result/${id}`,
              {
                method: 'PATCH',
                body: form
              }
            )
              .then(res => res.json())
              .then(json => { resultContext.setResult(json) })
              .catch(err => {
                console.error(err);
                setAccepted(!val);
              })
          }}
        >
          {
            (accepted) ?
              <FontAwesomeIcon icon={faCheckCircle} />
              :
              <FontAwesomeIcon icon={faCircleXmark} />

          }
        </button>
      </div>
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
  const [plotLoading, setPlotLoading] = useState(false);
  const [result, setResult] = useState({});
  const [wellSelectionKey, setWellSelectionKey] = useState('all')
  const [wellSelection, setWellSelection] = useState([])
  const { id } = useParams();

  const getTestMinusControl = (testWells, controlWells) => {
    const concs = Array.from(new Set(controlWells
      .map(item => item.compound_concentration)
      .concat(testWells
        .map(item => item.compound_concentration)
      )
    )
    )
    const testMinusControl = concs.map(conc => {
      const controlWell = controlWells.filter(item => item.compound_concentration === conc)[0];
      const testWell = testWells.filter(item => item.compound_concentration === conc)[0];
      const correctedAbsorbance = testWell.absorbance.map(item => {
        const controlAbsorbance = controlWell.absorbance.filter(item_ => item.wavelength === item_.wavelength)[0]
        return { ...controlAbsorbance, absorbance: item.absorbance - controlAbsorbance.absorbance }
      }
      );
      return { ...testWell, absorbance: correctedAbsorbance }
    }
    )

    return testMinusControl;
  }

  const getDifference = (testMinusControl) => {
    return testMinusControl.map(well => {
      const zeroConcWell = testMinusControl.filter(item => item.compound_concentration === 0)[0]
      const diffAbsorbance = well.absorbance.map(item => {
        const refAbsorbance = zeroConcWell.absorbance.filter(item_ => item_.wavelength === item.wavelength)[0]

        return { ...item, absorbance: item.absorbance - refAbsorbance.absorbance }
      })
      return { ...well, absorbance: diffAbsorbance }
    })
  }

  const updateWellSelection = (wellSelectionKey) => {
    setWellSelectionKey(wellSelectionKey);
    const testWells = result.wells.filter(item => item.protein_concentration > 0)
    const controlWells = result.wells.filter(item => item.protein_concentration === 0)

    switch (wellSelectionKey) {
      case 'test':
        setWellSelection(testWells)
        break
      case 'control':
        setWellSelection(controlWells)
        break
      case 'test-minus-control':
        setWellSelection(getTestMinusControl(testWells, controlWells))
        break
      case 'diff':
        setWellSelection(getDifference(getTestMinusControl(testWells, controlWells)))
        break
      default:
        setWellSelection(result.wells);
    }
  }

  useEffect(() => {
    fetch(`http://localhost:8008/result/${id}`)
      .then(res => res.json())
      .then(json => {
        setResult(json);
        setWellSelection(json.wells);
      })
      .then(() => { setLoading(false) })
      .catch(err => { console.error(err) })

  }, [id])

  return <div className='page'>
    <ResultContext.Provider value={{ ...result, setResult: setResult }}>
      <div className='result-container'>
        <ResultNavigation {...result} />
        {loading ?? <Spinner />}
        <div className='main-content'>
          <div className='row'>
            <Compound {...result?.compound} />
            <ProteinCard {...result?.protein} />
            {/* <Protein {...result?.protein} /> */}
            <ResultAnnotate checked={result.checked} accepted={result.accepted} />
          </div>
        </div>
        <div className='col'>
          <div className='box'>
            <div className='main-content'>
              <ResponsePlot
                km={result?.km}
                vmax={result?.vmax}
                dose_response={result?.dose_response}
              />
              <ResultTable {...result} />
              <ResultResponseTable data={result?.dose_response} result_id={result?.id} setResult={setResult} />
            </div>
          </div>
          <div className='box main-content'>
            <AbsorbancePlotMultiple data={wellSelection} />
            <div className='col'>
              <div>
                {
                  plotLoading ? <FontAwesomeIcon icon={faHourglassStart} /> : <></>
                }
              </div>
              {/*
              <select onChange={event => {
                setPlotLoading(true);
                const wellSelectionKey = event.target.value;
                updateWellSelection(wellSelectionKey);
                setPlotLoading(false);
              }}
                value={wellSelectionKey}
              >
                <option value='test-minus-control'>test minus control</option>
                <option value='diff'>diff</option>
                <option value=''>all</option>
                <option value='test'>test</option>
                <option value='control'>control</option>
              </select>
              */}
              <table className="result-table">
                <tbody>
                  {
                    [
                      { name: 'All Traces', value: 'all' },
                      { name: 'Test Minus Control', value: 'test-minus-control' },
                      { name: 'Control Traces', value: 'control' },
                      { name: 'Test Traces', value: 'test' },
                      { name: 'Difference Traces', value: 'diff' },
                    ].map((item, idx) =>
                      <tr key={idx}>
                        <td>
                          <input type='checkbox'
                            checked={wellSelectionKey === item.value}
                            onChange={(event) => {
                              const wellSelectionKey = item.value;
                              setWellSelectionKey(wellSelectionKey);
                              updateWellSelection(wellSelectionKey);
                            }}
                          />
                        </td>
                        <td>
                          {item.name}
                        </td>
                      </tr>
                    )
                  }
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </ResultContext.Provider >
  </div >
}

ResultPage.propTypes = {
  id: PropTypes.number,
}
