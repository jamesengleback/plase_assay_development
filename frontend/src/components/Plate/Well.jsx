import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as d3 from 'd3';
import infernoScale from '../Absorbance/colors.jsx';

import CloseIcon from '../Icons/CloseIcon';
import AbsorbancePlot from '../Absorbance/AbsorbancePlot.jsx';

import plateStyles from './Plate.module.css';
import wellStyles from './Well.module.css';

function WellModal(props) {
  const [wellData, setWellData] = useState({})

  console.log('well modal props: ', props)

  useEffect(() => {
    fetch(`http://localhost:8008/well/${props.id}/detail`)
      .then(res => res.json())
      .then(json => {
        console.log('well-modal data: ', json)
        setWellData(json)
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
    <div className={wellStyles.wellModalOverlay}
      onClick={closeModal}
    >
      <div className={wellStyles.wellModal}>
        <button className={wellStyles.wellModalCloseButton} onClick={closeModal}>
          <CloseIcon {...props} />
        </button>
        <div>
          <strong>{wellData.address} </strong>
        </div>
        <div>
          <div>
            <div> <span> <strong>Total Volume:</strong> {wellData.total_volume} ul </span></div>
            <div> <span> <strong>Compound:</strong>{wellData?.compound?.name}</span></div>
            <div> <span> <strong>Compound Concentration:</strong>{wellData.compound_concentration} uM </span></div>
            <div> <span> <strong>Protein:</strong>{wellData?.protein?.name}</span></div>
            <div> <span> <strong>[Protein]:</strong>{wellData.protein_concentration} uM </span></div>
            <div> <span> <strong>File:</strong>{wellData.plate_file_id}</span></div>
            <div> <span> <strong>Result:</strong>{wellData.result_id}</span></div>
          </div>
          <hr />
          <div>
            <AbsorbancePlot data={wellData.absorbance} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Well(props) {
  const [expand, setExpand] = useState(false)
  const [modalExpand, setModalExpand] = useState(false)

  //let color_
  //switch (props.color) {
  //  case 'compound_concentration':
  //    color_ = colorScale(props.compound_concentration / 500)
  //  default: // volume
  //    color_ = colorScale(props.total_volume / 50)
  //}
  //const color = color_ // hate this

  let backgroundColor;

  switch (props.color) {
    case 'compound_concentration':
      backgroundColor = props.compound_concentration !== null ? infernoScale(props.compound_concentration / 500) : '#202325'; // Handle null values
      break;
    case 'protein_concentration':
      backgroundColor = props.protein_concentration !== null ? infernoScale(props.protein_concentration / 10) : '#202325'; // Example with a different scale and max
      break;
    case 'total_volume':
      backgroundColor = props.total_volume !== null ? infernoScale(props.total_volume / 50) : '#202325'; // Handle null values
      break;
    case 'result_id':
      //const color = d3.scaleSequential(d3.interpolateRainbow);
      const color = d3.scaleOrdinal(d3.schemeTableau10);
      backgroundColor = props.result_id !== null ? d3.schemeTableau10[props.result_id % d3.schemeTableau10.length] : '#202325'; // Handle null values
      break;
    // Add more cases for other props.color values as needed
    default: // Default to coloring by total volume if props.color is not recognized
      backgroundColor = props.total_volume !== null ? infernoScale(props.total_volume / 50) : '#202325'; // Handle null values
  }
  return (
    <div className={plateStyles.plateWell}
      style={{ backgroundColor: backgroundColor }}
      onMouseEnter={event => { setExpand(true) }}
      onMouseLeave={event => { setExpand(false) }}
      onClick={event => { setModalExpand(true); setExpand(false) }}
    >
      {
        expand ? <div className={plateStyles.plateWellExpand}>
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
