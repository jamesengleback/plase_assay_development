import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import ResponsePlot from './ResponsePlot';
import ResultResponseTable from './ResultResponseTable';
import Compound from '../Compound/Compound';
import styles from './Result.module.css'

export function ResultTable(props) {
  return (
    <div className={styles.tableContainer}>
      <table className={styles.resultTable}>
        <tbody>
          {/*
            <tr>
              <th colSpan="2">Michaelis Menten Parameters</th>
            </tr>
          */}
          <tr>
            <th>K<sub>m</sub></th>
            <td>{props.km ? props.km.toFixed(3) : 'N/A'}</td>
          </tr>
          <tr>
            <th>V<sub>max</sub></th>
            <td>{props.vmax ? props.vmax.toFixed(3) : 'N/A'}</td>
          </tr>
          <tr>
            <th>R<sup>2</sup></th>
            <td>{props.r_squared ? props.r_squared.toFixed(3) : 'N/A'}</td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

export default function Result(props) {

  return (
    <div className={styles.summaryCard}>
      <h3 className={styles.compoundName}>
        <Link to={`/experiment/${props.experiment_id}`}>
          Experiment {props.experiment_id}
        </Link>
        <span> / </span>
        <Link to={`/result/${props.id}`}>
          Result {props.id} {props.compound?.name || 'Unknown Compound'}
        </Link>
      </h3>

      <div className={styles.row}>
        <div className={styles.leftColumn}>
          <div className={styles.tableContainer}>
            <table className={styles.resultTable}>
              <tbody>
                <tr>
                  <th colSpan="2">Michaelis Menten Parameters</th>
                </tr>
                <tr>
                  <th>K<sub>m</sub></th>
                  <td>{props.km ? props.km.toFixed(3) : 'N/A'}</td>
                </tr>
                <tr>
                  <th>V<sub>max</sub></th>
                  <td>{props.vmax ? props.vmax.toFixed(3) : 'N/A'}</td>
                </tr>
                <tr>
                  <th>R<sup>2</sup></th>
                  <td>{props.r_squared ? props.r_squared.toFixed(3) : 'N/A'}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div className={styles.rightColumn}>
          <Compound {...props?.compound} />
        </div>
      </div>
      <div className={styles.responsePlotContainer}>
        <ResponsePlot
          km={props.km}
          vmax={props.vmax}
          dose_response={props.dose_response}
        />
      </div>
    </div>
  );
}

Result.propTypes = {
  id: PropTypes.number,
  experiment_id: PropTypes.number,
  km: PropTypes.number,
  vmax: PropTypes.number,
  r_squared: PropTypes.number,
  dose_response: PropTypes.arrayOf(
    PropTypes.shape({
      concentration: PropTypes.number.isRequired,
      response: PropTypes.number.isRequired,
    })
  ),
  compound: PropTypes.shape({
    id: PropTypes.number,
    canonical_smiles: PropTypes.string,
    name: PropTypes.string,
    svg: PropTypes.string,
    mw: PropTypes.number,
  }),
};
//import { useState, useEffect } from 'react';
//import PropTypes from 'prop-types';
//import { Link } from 'react-router-dom';
//import ResponsePlot from './ResponsePlot';
//import Compound from '../Compound/Compound';
//import './Result.css'
//
//export default function Result(props) {
//  console.log('result ', props)
//
//  return <>
//    <div className="summary-card">
//      <h3 className="compound-name">
//        <Link to={`/result/${props.id}`}>
//          Result {props.id} {props.compound?.name || 'Unknown Compound'}
//        </Link>
//      </h3>
//        <div className="row">
//          <table className="result-table">
//            <tbody>
//              <tr>
//                <th colSpan="2">Compound Information</th>
//              </tr>
//              <tr>
//                <th>K<sub>m</sub></th>
//                <td>{props.km ? props.km.toFixed(3) : 'N/A'}</td>
//              </tr>
//              <tr>
//                <th>V<sub>max</sub></th>
//                <td>{props.vmax ? props.vmax.toFixed(3) : 'N/A'}</td>
//              </tr>
//              <tr>
//                <th>R<sup>2</sup></th>
//                <td>{props.r_squared ? props.r_squared.toFixed(3) : 'N/A'}</td>
//              </tr>
//              <tr>
//                <th>MW</th>
//                <td>{props.compound?.mw ? props.compound.mw.toFixed(1) : 'N/A'}</td>
//              </tr>
//            </tbody>
//          </table>
//          <div className="response-plot-container">
//            <Compound {...props?.compound} />
//          </div>
//        </div>
//      <div className="response-plot-container">
//        <ResponsePlot
//          km={props.km}
//          vmax={props.vmax}
//          dose_response={props.dose_response}
//        />
//      </div>
//    </div>
//  </>
//}
//
//Result.propTypes = {
//  data: PropTypes.shape({
//    id: PropTypes.number,
//    km: PropTypes.number,
//    vmax: PropTypes.number,
//    r_squared: PropTypes.number,
//    dose_response: PropTypes.arrayOf(
//      PropTypes.shape({
//        concentration: PropTypes.number.isRequired,
//        response: PropTypes.number.isRequired,
//      })
//    ),
//    compound: PropTypes.shape({
//      id: PropTypes.number,
//      canonical_smiles: PropTypes.string,
//      name: PropTypes.string,
//      svg: PropTypes.string,
//      mw: PropTypes.number,
//    }),
//  }),
//};
