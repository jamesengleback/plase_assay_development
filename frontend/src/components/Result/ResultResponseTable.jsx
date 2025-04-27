import * as d3 from 'd3';
import './Result.css'
import PropTypes from 'prop-types';

export default function ResultResponseTable(props) {
  const setResult = props.setResult
  console.warn(props)
  if (!props.data || props.data.length === 0) {
    return <p>No response data available.</p>;
  }
  return (
    <div className='table-container'>
      <table className="result-table">
        <thead>
          <tr>
            <th>Concentration</th>
            <th>Response</th>
            <th>Exclude</th>
          </tr>
        </thead>
        <tbody>
          {props?.data.map(item => (
            <tr key={item.id}>
              <td>{item.concentration.toFixed(2)}</td>
              <td>{item.response.toFixed(3)}</td>
              <td>
                <input type='checkbox'
                  defaultChecked={item.exclude}
                  onChange={(event) => {
                    const form = new FormData()
                    form.append('exclude_id', item.id)
                    form.append('exclude', event.target.checked)
                    fetch(`http://localhost:8008/result/${props.result_id}`,
                      {
                        method: 'PATCH',
                        body: form
                      }
                    )
                      .then(res => res.json())
                      .then(json => { console.warn(json); return json })
                      .then(json => { setResult(json) })
                      .catch(err => { console.error(err) })
                  }}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
};

ResultResponseTable.PropTypes = {
  data: PropTypes.shape({
    id: PropTypes.number,
    concentration: PropTypes.number,
    response: PropTypes.number,
    result_id: PropTypes.number,
    exclude: PropTypes.bool,
  }),
  result_id: PropTypes.number,
  setResult: PropTypes.func
}
