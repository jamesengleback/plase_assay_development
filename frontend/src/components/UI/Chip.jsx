import React from 'react'
import './Chip.css'

export default function Chip(props) {
    const { icon, label, other } = props
    return (
        <div className='chip' {...props}>
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
