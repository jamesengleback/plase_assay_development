import React from 'react'
import styles from './Chip.module.css'

export default function Chip(props) {
    const { icon, label, other } = props
    return (
        <div className={styles.chip} {...props}>
            {
                icon ?
                    icon : null
            }
            {
                label ?
                    label : null
            }
        </div>
    )
}
