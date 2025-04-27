import PropTypes from 'prop-types';
import './Compound.css';

export default function Compound(props) {
    return (
        <div className='info-card'>
            <h3 className="compound-name">
                {props?.name || 'Unknown Compound'}
            </h3>
            <div>
                <strong>MW:</strong> {props?.mw ? props.mw.toFixed(1) : 'N/A'}
            </div>
            <div>
                <strong>SMILES:</strong> {props?.canonical_smiles ? props.canonical_smiles : 'N/A'}
            </div>
            <div>
                <img src={`data:image/svg+xml;utf8,${encodeURIComponent(props?.svg)}`}
                    height={200}
                    width={200}
                />
            </div>
        </div>
    )
};

Compound.propTypes = {
    id: PropTypes.number,
    canonical_smiles: PropTypes.string,
    name: PropTypes.string,
    svg: PropTypes.string,
    mw: PropTypes.number,
}
