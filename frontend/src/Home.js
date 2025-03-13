import { React, useState } from 'react';
import { DataGrid } from '@mui/x-data-grid';


const rows = [
    {'id':1, 'poop':'solid'},
    {'id':2, 'poop':'solid'},
    {'id':3, 'poop':'solid'}
]

const columns = [
    { field: 'id', headerName: 'id'},
    { field: 'poop', headerName: 'poop'}
]

export default function Home() {
    return (
        <>
            <DataGrid rows={rows} columns={columns} />
        </>
    )
}
