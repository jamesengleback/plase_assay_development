import React from 'react';
import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import TextField from '@mui/material/TextField';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';

export default function Search() {
    return (
        <>
            <FormControl>
                <TextField id='text-search' label='Search' sx={{ borderRadius: 10 }} />
                <Select id='select-experiment-number'
                    label='Experiment Number'
                >
                    <MenuItem value={1}> 1 </MenuItem>
                </Select>
            </FormControl>
        </>
    )
}

