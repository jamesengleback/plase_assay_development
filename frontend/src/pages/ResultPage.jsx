import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import PropTypes from 'prop-types';
import { ErrorBoundary } from 'react-error-boundary';

import { ResultTable } from '../components/Result/Result';
import ResultResponseTable from '../components/Result/ResultResponseTable';
import AbsorbancePlotMultiple from '../components/Absorbance/AbsorbancePlotMultiple';
import Compound from '../components/Compound/Compound';
import ProteinCard from '../components/Protein/ProteinCard';
import ResponsePlot from '../components/Result/ResponsePlot';
import ResultAnnotate from '../components/Result/ResultAnnotate';
import ResultTitle from '../components/Result/ResultTitle';
import Spinner from '../components/utils/Spinner/Spinner';

import { ResultContext } from '../components/Result/ResultContext';
import ResultNavigation from '../components/Result/ResultNavigation';


function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div role="alert">
      <p>Something went wrong:</p>
      <pre style={{ color: 'red' }}>{error.message}</pre>
      <button onClick={resetErrorBoundary}>Try again</button>
    </div>
  );
}

export default function ResultPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState({});
  const [wellSelectionKey, setWellSelectionKey] = useState('test-minus-control')
  const [wellSelection, setWellSelection] = useState([])
  const { id } = useParams();

  const getTestMinusControl = (testWells, controlWells) => {
    if (testWells === undefined || testWells.length === 0) {
      return controlWells
    } else if (controlWells === undefined || controlWells.length === 0) {
      return testWells
    }

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
      const correctedAbsorbance = testWell.absorbance?.map(item => {
        const controlAbsorbance = controlWell.absorbance?.filter(item_ => item.wavelength === item_.wavelength)[0]
        if (typeof controlAbsorbance === 'undefined') {
          return item

        } else {
          return { ...controlAbsorbance, absorbance: item.absorbance - controlAbsorbance.absorbance }
        }
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
        return json
      })
      .then(result => {
        const testWells = result.wells?.filter(item => item.protein_concentration > 0)
        const controlWells = result.wells?.filter(item => item.protein_concentration === 0)
        setWellSelection(getTestMinusControl(testWells, controlWells))
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      })
  }, [id])

  return <div className='page'>
    <ResultContext.Provider value={{ ...result, setResult: setResult }}>
      <div className='result-container'>
        <ResultNavigation {...result} />
        {loading ? <Spinner /> : <></>}
        <div style={{ padding: '1em' }}>
          {/* Absorbance Plot and Well Selection */}
          <div style={{ display: 'flex', gap: '1em', marginBottom: '1em', alignItems: 'flex-start' }}>
            <div style={{ flex: 3 }}>
              <ErrorBoundary fallback={ErrorFallback}>
                <AbsorbancePlotMultiple data={wellSelection} result={result} title={`Exp ${result?.experiment_id || 'N/A'} Result ${result?.id || 'N/A'}: ${result?.compound?.name || 'Unknown'} vs ${result?.protein?.name || 'Unknown'} - Absorbance Spectra (${wellSelectionKey.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())})`} />
              </ErrorBoundary>
            </div>
            <div style={{ flex: 1 }}>
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
                      }} style={{ cursor: 'pointer' }}>
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
          
          {/* Response Plot, Tables, and Annotations */}
          <div style={{ display: 'flex', gap: '1em', marginBottom: '1em', alignItems: 'flex-start', height: '500px' }}>
            <div style={{ flex: 2, height: '100%' }}>
              <ResponsePlot
                style={{ width: '100%', height: '100%' }}
                title={`Exp ${result?.experiment_id || 'N/A'} Result ${result?.id || 'N/A'}: ${result?.compound?.name || 'Unknown'} vs ${result?.protein?.name || 'Unknown'} - Dose-Response`}
                {...result}
              />
            </div>
            <div style={{ flex: 1 }}>
              <ResultResponseTable data={result?.dose_response} result_id={result?.id} setResult={setResult} />
            </div>
          </div>
          
          {/* Compound and Protein */}
          <div className='row'>
            <Compound {...result?.compound} />
            <ProteinCard {...result?.protein} />
            <ResultAnnotate {...result} />
          </div>
        </div>
      </div>
    </ResultContext.Provider >
  </div >
}

ResultPage.propTypes = {
  id: PropTypes.number,
}
