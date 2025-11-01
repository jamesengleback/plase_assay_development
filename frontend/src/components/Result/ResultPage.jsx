import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import PropTypes from 'prop-types';

import { ResultTable } from './Result';
import ResultResponseTable from './ResultResponseTable';
import AbsorbancePlotMultiple from '../Absorbance/AbsorbancePlotMultiple';
import Compound from '../Compound/Compound';
import ProteinCard from '../Protein/ProteinCard';
import ResponsePlot from './ResponsePlot';
import ResultAnnotate from './ResultAnnotate';
import ResultTitle from './ResultTitle';
import Spinner from '../utils/Spinner/Spinner';

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

import './Result.css'
import { ResultContext } from './ResultContext';
import ResultNavigation from './ResultNavigation';






export default function ResultPage(props) {
  const [loading, setLoading] = useState(true);
  const [plotLoading, setPlotLoading] = useState(false);
  const [result, setResult] = useState({});
  const [wellSelectionKey, setWellSelectionKey] = useState('test-minus-control')
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

  const selectWells = (result, key) => {
    const testWells = result.wells?.filter(item => item.protein_concentration > 0)
    const controlWells = result.wells?.filter(item => item.protein_concentration === 0)

    switch (key) {
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
    if (result.wells) {
      selectWells(result, wellSelectionKey)
    }
  }, [result, wellSelectionKey])

  useEffect(() => {
    setLoading(true);
    fetch(`http://localhost:8008/result/${id}`)
      .then(res => res.json())
      .then(json => {
        setResult(json);
        setLoading(false);
        return json
      })
      .then(result => {
        const testWells = result.wells?.filter(item => item.protein_concentration > 0)
        const controlWells = result.wells?.filter(item => item.protein_concentration === 0)
        setWellSelection(getTestMinusControl(testWells, controlWells))
      })
      .catch(err => {
        console.error(err);
      })
  }, [id])

  return <div className='page'>
    <ResultContext.Provider value={{ ...result, setResult: setResult }}>
      <div className='result-container'>
        <ResultNavigation {...result} />
        {loading ?? <Spinner />}
        {/* <div className='row' style={{ justifyContent: 'space-between' }}> */}
        {/*   <ResultTitle {...result} /> */}
        {/*   <ResultAnnotate checked={result.checked} accepted={result.accepted} /> */}
        {/* </div> */}
        <div className='col' style={{ alignItems: 'flex-end', padding: '1em' }}>
          <div className='main-content'>
            <AbsorbancePlotMultiple data={wellSelection} result={result} />
            <div className='col'>
              <div>
                {
                  plotLoading ? <FontAwesomeIcon icon={faHourglassStart} /> : <></>
                }
              </div>
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
                      <tr key={idx} onClick={() => {
                        setWellSelectionKey(item.value);

                      }
                      } style={{ cursor: 'pointer' }}>
                        <td>
                          <input type='checkbox'
                            checked={wellSelectionKey === item.value}
                            onChange={() => { }}
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
          <div className='main-content' >
            <ResponsePlot
              style={{ width: '100%' }}
              {...result}
            />
            <ResultTable {...result} />
            <ResultResponseTable data={result?.dose_response} result_id={result?.id} setResult={setResult} />
            <ResultAnnotate {...result} />
          </div>
        </div>
        {/* <div className='col'> */}
        {/* <div className='row'> */}
        {/*   <Compound {...result?.compound} /> */}
        {/*   <ProteinCard {...result?.protein} /> */}
        {/*   {/* <Protein {...result?.protein} /> */}
        {/*   <ResultAnnotate checked={result.checked} accepted={result.accepted} /> */}
        {/* </div> */}
        {/* </div> */}
      </div>
    </ResultContext.Provider >
  </div >
}

ResultPage.propTypes = {
  id: PropTypes.number,
}
