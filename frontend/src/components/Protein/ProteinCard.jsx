import { useState } from 'react';
import PropTypes from 'prop-types';
import './Protein.css'; // Assuming you'll name your CSS file this

const AAColors = {
    A: '#c4bfb7',
    C: '#88bf9d',
    D: '#92c281',
    E: '#9a9184',
    F: '#a1998d',
    G: '#a49d91',
    H: '#a69e92',
    I: '#ada69c',
    K: '#b9b3aa',
    L: '#bdaf94',
    M: '#c377a7',
    N: '#7be3f7',
    P: '#c9c5be',
    Q: '#cfcbc4',
    R: '#d4d1cb',
    S: '#d9dc52',
    T: '#ecb052',
    V: '#f0eb7d',
    W: '#b9b3aa',
    Y: '#ff5e64'
};

function Tooltip({ label }) {
    console.warn(label);
    return <div className="tooltip"> {label} </div>;
}

Tooltip.propTypes = {
    label: PropTypes.string.isRequired,
};

function AA({ id, letter }) {
    const [isHovered, setIsHovered] = useState(false);
    const aaStyle = {
        color: AAColors[letter],
    };
    const aaHighlightStyle = {
        color: 'white',
        backgroundColor: AAColors[letter],
        fontWeight: 'bold',
    };

    return (
        <div
            id={id}
            className="amino-acid"
            style={isHovered ? aaHighlightStyle : aaStyle}
            onMouseOver={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {letter}
            {isHovered && <Tooltip label={`${letter}${id}`} />}
        </div>
    );
}

AA.propTypes = {
    id: PropTypes.string.isRequired,
    letter: PropTypes.string.isRequired,
};

function Sequence({ sequence }) {
    return (
        <div className="sequence">
            {sequence ? (
                sequence.split('').map((aa, idx) => (
                    <AA
                        id={idx}
                        key={idx}
                        letter={aa}
                    />
                ))
            ) : null}
        </div>
    );
}

Sequence.propTypes = {
    sequence: PropTypes.string,
};

export default function ProteinCard({ name, accession, species, sequence }) {
    return (
        <div className="info-card">
            <div className="protein-header">
                <h5 className="protein-name"> Name: <span className="protein-value"> {name} </span> </h5>
                <h5 className="protein-accession"> Accession: <span className="protein-value"> {accession} </span> </h5>
                <h5 className="protein-species"> Species: <span className="protein-value"> {species} </span></h5>
            </div>
            <div>
                <Sequence sequence={sequence} />
            </div>
        </div>
    );
}

ProteinCard.propTypes = {
    name: PropTypes.string.isRequired,
    accession: PropTypes.string,
    species: PropTypes.string,
}
