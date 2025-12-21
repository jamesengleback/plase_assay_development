import { useState, useEffect } from 'react'; // <-- Import hooks
import PropTypes from 'prop-types';

// Define your API base URL (adjust if needed)
const API_BASE_URL = 'http://localhost:8008/compound/';

export default function Compound({ id, name, canonical_smiles, mw, svg }) {
    // Destructure initial/fallback props for clarity

    // 1. State to hold the detailed compound data fetched from the API
    const [compoundData, setCompoundData] = useState({
        name,
        canonical_smiles,
        mw,
        svg,
        loading: true,
        error: null
    });

    // 2. useEffect hook to fetch data when the 'id' prop changes
    useEffect(() => {
        // Only run the effect if an ID is provided
        if (!id) {
            setCompoundData(prev => ({ ...prev, loading: false }));
            return;
        }

        const fetchCompoundDetails = async () => {
            setCompoundData(prev => ({ ...prev, loading: true, error: null })); // Start loading

            try {
                const response = await fetch(`${API_BASE_URL}${id}`);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                setCompoundData({
                    ...data,
                    loading: false,
                    error: null
                });

            } catch (error) {
                console.error("Failed to fetch compound data:", error);
                setCompoundData(prev => ({
                    ...prev,
                    loading: false,
                    error: "Failed to load data. Please check the network."
                }));
            }
        };

        fetchCompoundDetails();

    }, [id]); // Dependency array: Re-run effect only when 'id' changes


    if (compoundData.loading) {
        return <div className='info-card'>Loading Compound Data...</div>;
    }

    if (compoundData.error) {
        return <div className='info-card error'>Error: {compoundData.error}</div>;
    }

    // Use compoundData for rendering
    const compoundName = compoundData.name || 'Unknown Compound';
    const molecularWeight = compoundData.mw;
    const smiles = compoundData.canonical_smiles;
    const svgContent = compoundData.svg;

    return (
        <div className='info-card'>
            <h3 className="compound-name">
                {compoundName} (ID: {id})
            </h3>
            <hr />
            <div>
                <strong>MW:</strong> {molecularWeight ? molecularWeight.toFixed(2) : 'N/A'}
            </div>
            {/* Conditional rendering for the structure image */}
            {svgContent ? (
                <div>
                    <img
                        src={`data:image/svg+xml;utf8,${encodeURIComponent(svgContent)}`}
                        alt={`Structure of ${compoundName}`}
                        style={{ width: '100%', height: 'auto' }}
                    />
                </div>
            ) : (
                <p>Structure SVG not available.</p>
            )}
            <div>
                <strong>SMILES:</strong> {smiles ? smiles : 'N/A'}
            </div>
        </div>
    );
}

Compound.propTypes = {
    // The ID is now the key prop used to trigger the fetch
    id: PropTypes.number.isRequired,
    // Other props are optional fallback/initial data
    canonical_smiles: PropTypes.string,
    name: PropTypes.string,
    svg: PropTypes.string,
    mw: PropTypes.number,
}
// import PropTypes from 'prop-types';
// import './Compound.css';
//
// export default function Compound(props) {
//     debugger
//     return (
//         <div className='info-card'>
//             <h3 className="compound-name">
//                 {props?.name || 'Unknown Compound'}
//             </h3>
//             <div>
//                 <strong>MW:</strong> {props?.mw ? props.mw.toFixed(1) : 'N/A'}
//             </div>
//             <div>
//                 <strong>SMILES:</strong> {props?.canonical_smiles ? props.canonical_smiles : 'N/A'}
//             </div>
//             <div>
//                 <img src={`data:image/svg+xml;utf8,${encodeURIComponent(props?.svg)}`}
//                     height={200}
//                     width={200}
//                 />
//             </div>
//         </div>
//     )
// };
//
// Compound.propTypes = {
//     id: PropTypes.number,
//     canonical_smiles: PropTypes.string,
//     name: PropTypes.string,
//     svg: PropTypes.string,
//     mw: PropTypes.number,
// }

