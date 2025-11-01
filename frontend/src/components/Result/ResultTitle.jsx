import { ResultTable } from './Result';

export default function ResultTitle(props) {
  return (
    <div className="result-title">
      <h2>{props.compound?.name} / {props.protein?.name}</h2>
    </div>
  )
}
