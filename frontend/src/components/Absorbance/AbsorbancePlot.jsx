import { useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as d3 from 'd3';


export default function AbsorbancePlot(props) {

  //console.log(props, props?.data?.length);

  const svgRef = useRef();
  const margin = { top: 20, right: 30, bottom: 35, left: 50 };
  const width = 400 - margin.left - margin.right;
  const height = 200 - margin.top - margin.bottom;

  console.log(props.data)

  useEffect(() => {
    if (props?.data?.length > 0) {
    const svg = d3.select(svgRef.current)
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .style("background-color", '#eee');

    svg.select("g").remove()
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`); // Apply margin translation here

    const validData = props.data.filter(d =>
      typeof d?.wavelength === 'number' && !isNaN(d.wavelength) &&
      typeof d?.absorbance === 'number' && !isNaN(d.absorbance)
    );

    const xScale = d3.scaleLinear()
      .domain([d3.min(validData, d => d.wavelength), d3.max(validData, d => d.wavelength)])
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain([0, 1])
      //.domain([0, d3.max(validData, d => d.absorbance)])
      .range([height, 0]);

    g.append('g')
      .attr('transform', `translate(0, ${height})`) // Translate the x-axis within the 'g'
      .call(d3.axisBottom(xScale));

    g.append('g')
      .call(d3.axisLeft(yScale));

    g.selectAll(".y-label")
      .data(["Absorbance"])
      .join(
        enter => enter.append("text")
          .attr("class", "y-label")
          .attr("transform", "rotate(-90)")
          .attr("y", 0 - margin.left)
          .attr("x", 0 - (height / 2))
          .attr("dy", "1em")
          .style("text-anchor", "middle")
          .text(d => d),
        update => update.text(d => d),
        exit => exit.remove()
      );

    g.selectAll(".x-label")
      .data(["Wavelength"])
      .join(
        enter => enter
          .append("text")
          .attr("class", "x-label")
          .attr("transform", `translate(${width / 2}, ${height + margin.bottom})`)
          .style("text-anchor", "middle")
          .text(d => d),
        update => update.text(d => d),
        exit => exit.remove()
      );

    const line = d3.line()
      .x(d => xScale(d.wavelength))
      .y(d => yScale(d.absorbance));

    g.append('path') // append the path to the 'g' element
      .datum(validData)
      .attr("d", line)
      .attr("class", "line")
      .attr("fill", "none")
      .attr("stroke", "steelblue")
      .attr("stroke-width", 1.5)
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round");
    }
  }, [props.data]);

  return (
    <>
      <svg ref={svgRef}>
      </svg>
    </>
  );
}

AbsorbancePlot.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number,
      plate_data_file_id: PropTypes.number,
      well_id: PropTypes.number,
      wavelength: PropTypes.number,
      absorbance: PropTypes.number
    }
    )
  )
}
