import { Link } from 'react-router-dom';
import './Nav.css';


export default function Nav(props) {
    return (
        <nav>
            {
                props.routes.map((item, idx) => (
                    <ul key={idx}>
                        <li> <Link to={item.href}>{item.name}</Link> </li>
                    </ul>
                ))
            }
        </nav>
    )
}
