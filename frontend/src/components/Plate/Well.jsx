import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import './Plate.css';
import './Well.css';
import CloseIcon from '../Icons/CloseIcon';
import AbsorbancePlot from '../Absorbance/AbsorbancePlot.jsx';

function WellModal(props) {
  const [absorbance, setAbsorbance] = useState([])
  const [wellData, setWellData] = useState({})

  useEffect(() => {
    fetch(`http://localhost:8008/well/${props.id}/detail`)
      .then(res => res.json())
      .then(json => {
        setWellData(json)
        setAbsorbance(json.absorbance)
      })
      .catch(err => { console.error(err) })
  },
    [])
  const closeModal = (event) => {
    event.stopPropagation()
    props?.setModalExpand(false);
    props?.setExpand(false);
  }
  return (
    <div className='well-modal-overlay'
      onClick={closeModal}
    >
      <div className='well-modal'>
        <button className='well-modal-close-button' onClick={closeModal}>
          <CloseIcon {...props} />
        </button>
        <div>
          <strong>{props.address} </strong>
        </div>
        <div>
          <div>
            <div> <span> <strong>Total Volume:</strong> {props.total_volume} ul </span></div>
            <div> <span> <strong>Compound:</strong>{wellData?.compound?.name}</span></div>
            <div> <span> <strong>Compound Concentration:</strong>{props.compound_concentration} uM </span></div>
            <div> <span> <strong>Protein:</strong>{wellData?.protein?.name}</span></div>
            <div> <span> <strong>[Protein]:</strong>{props.protein_concentration} uM </span></div>
            <div> <span> <strong>File:</strong>{props.file_id}</span></div>
            <div> <span> <strong>Result:</strong>{props.result_id}</span></div>
          </div>
          <hr />
          <div>
            <AbsorbancePlot data={absorbance} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Well(props) {
  const [expand, setExpand] = useState(false)
  const [modalExpand, setModalExpand] = useState(false)
  return (
    <div className='plate-well'
      onMouseEnter={event => { setExpand(true) }}
      onMouseLeave={event => { setExpand(false) }}
      onClick={event => { setModalExpand(true); setExpand(false) }}
    >
      {
        expand ? <div className='plate-well-expand'>
          <div>
            <strong>{props.address} </strong>
          </div>
          <hr />
          <div>
            <div> <span> <strong>Total Volume:</strong> {props.total_volume} ul </span></div>
            <div> <span> <strong>Compound:</strong>{props.compound_id}</span></div>
            <div> <span> <strong>Compound Concentration:</strong>{props.compound_concentration} uM </span></div>
            <div> <span> <strong>Protein:</strong>{props.protein_id}</span></div>
            <div> <span> <strong>[Protein]:</strong>{props.protein_concentration} uM </span></div>
            <div> <span> <strong>File:</strong>{props.file_id}</span></div>
            <div> <span> <strong>Result:</strong>{props.result_id}</span></div>
          </div>
        </div>
          :
          <>
          </>
      }

      {
        modalExpand ?
          <WellModal {...{ setModalExpand: setModalExpand, setExpand: setExpand, ...props }} />
          :
          <></>
      }
    </div>
  )
}


Well.propTypes = {
  id: PropTypes.number,
  address: PropTypes.string,

  compound_id: PropTypes.number,
  file_id: PropTypes.number,
  plate_id: PropTypes.number,
  protein_id: PropTypes.number,
  result_id: PropTypes.number,

  protein_concentration: PropTypes.number,
  total_volume: PropTypes.number,
  compound_concentration: PropTypes.number,
}
