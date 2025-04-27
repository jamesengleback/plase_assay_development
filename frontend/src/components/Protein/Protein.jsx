import PropTypes from 'prop-types';
import './Protein.css';

const aminoAcidColors = {
    // Nonpolar, Aliphatic (often found in protein interiors)
    'G': '#fbf1c7', // Glycine (small, flexible) - light, neutral
    'A': '#ebdbb2', // Alanine (small, hydrophobic) - slightly darker neutral
    'V': '#8ec07c', // Valine (branched, hydrophobic) - green for aliphatic
    'L': '#83a598', // Leucine (branched, hydrophobic) - another shade of green/teal
    'I': '#427b58', // Isoleucine (branched, hydrophobic) - darker green

    // Aromatic (often involved in interactions and UV absorption)
    'F': '#fabd2f', // Phenylalanine - yellow for aromatic ring
    'W': '#fe8019', // Tryptophan - orange, larger aromatic
    'Y': '#d3869b', // Tyrosine (can be polar due to -OH) - pinkish

    // Polar, Uncharged (can form hydrogen bonds)
    'S': '#f2e5bc', // Serine (-OH) - light, slightly warm
    'T': '#d5c4a1', // Threonine (-OH) - slightly darker warm
    'C': '#b8bb26', // Cysteine (-SH) - yellowish-green (sulfur)
    'N': '#bdae93', // Asparagine (amide) - muted neutral
    'Q': '#a89984', // Glutamine (amide) - slightly darker muted neutral

    // Charged (important for electrostatic interactions)
    'D': '#9d0006', // Aspartic Acid (negative) - red for negative charge
    'E': '#af3a03', // Glutamic Acid (negative) - another shade of red/orange
    'K': '#076678', // Lysine (positive) - blue/teal for positive charge
    'R': '#3c3836', // Arginine (positive, bulky) - darker, strong color
    'H': '#8f3f71', // Histidine (positive/aromatic, pKa near neutral) - purple

    // Special Cases
    'P': '#b57614', // Proline (cyclic, helix breaker) - brownish/orange
    'M': '#79740e', // Methionine (sulfur, but hydrophobic) - olive/dark yellow
};

export default function Protein(props) {
    const formatSequenceWithColors = (sequence) => {
        if (!sequence) {
            return null;
        }
        return sequence.split('').map((aminoAcid, index) => (
            <>
                <code key={index} style={{ backgroundColor: aminoAcidColors[aminoAcid.toUpperCase()] || 'white' }}>
                    {aminoAcid}
                </code>
                {
                    (index % 20 === 0 && index > 0) ?
                        <>
                            <code> {index} </code>
                            <br />
                        </>
                        :
                        <></>
                }
            </>
        ));
    };
    const formatSequence = (sequence) => {
        if (!sequence) {
            return null;
        }
        return sequence.match(/.{1,20}/g)?.map((segment, index) => (
            <span key={index}>
                <code>{segment}</code>
                {index < sequence.length / 20 - 1 ? <> <code> {(index + 1) * segment.length} </code><br /></> : ''} {/* Add line break except for the last segment */}
            </span>
        ));
    };

    return (
        <div className='info-card protein-card'>
            <span><strong>{props.name}</strong></span>
            <div className='protein-sequence'>
                {formatSequenceWithColors(props.sequence) || <></>}
            </div>
        </div>
    )
};


Protein.propTypes = PropTypes.shape({
    id: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired,
    sequence: PropTypes.string,
    purification: PropTypes.string,
});
