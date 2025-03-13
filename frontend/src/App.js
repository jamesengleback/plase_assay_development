import { React, useState } from 'react';
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Link } from 'react-router-dom';

import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import Divider from '@mui/material/Divider';
import { createTheme, ThemeProvider } from '@mui/material/styles';

import HomeIcon from '@mui/icons-material/Home';
import SearchIcon from '@mui/icons-material/Search';

import Home from './Home.js';
import Search from './Search.js';

const theme = createTheme({
    palette: {
        text: {
            primary: '#111',
            secondary: '#222'
        },
        background: {
            box: '#fff',
            paper: '#ff5e64',
        },
    }
});

function LeftDrawer(props) {

    const [drawerOpen, setDrawerOpen] = useState(false);

    return (
        <Drawer open={true} variant='permanent' sx={{
            '& .MuiDrawer-paper': {
                width: 80,
                boxSizing: 'border-box'
            }
        }}>
            <List>

                <ListItem>
                    <ListItemButton>
                        <Link to='/'>
                            <ListItemIcon>
                                <HomeIcon />
                            </ListItemIcon>
                        </Link>
                    </ListItemButton>
                </ListItem>

                <Divider />

                <ListItem>
                    <ListItemButton>
                        <Link to='/search'>
                            <ListItemIcon>
                                <SearchIcon />
                            </ListItemIcon>
                        </Link>
                    </ListItemButton>
                </ListItem>

            </List>
        </Drawer>
    )
}

export default function App() {

    return (
        <>
            <BrowserRouter>
                <ThemeProvider theme={theme}>
                    <LeftDrawer />
                    <Container maxWidth='lg'>
                        <Box sx={{
                            marginLeft: 8,
                            backgroundColor: 'background.box',
                            height: '100%',
                            width: '100%',
                        }}
                        >
                            <Routes>
                                <Route path="/" element={<Home />} />
                                <Route path="/search" element={<Search />} />
                            </Routes>
                        </Box>
                    </Container>
                </ThemeProvider>
            </BrowserRouter>
        </>
    )
}
