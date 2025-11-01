import React, { useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as d3 from 'd3';
import infernoScale, { responsePlotColors } from './colors.jsx';

export default function AbsorbancePlotMultiple({ data, result }) {
  // console.log(result.dose_response)
  const excludeDict = result?.dose_response && Object.fromEntries(result?.dose_response?.map(i => [i.concentration, i.exclude]))
  const svgRef = useRef();
  const margin = { top: 20, right: 30, bottom: 45, left: 60 };
  const width = (window.innerWidth * 0.8) - margin.left - margin.right;
  const height = 400 - margin.top - margin.bottom;
  const limits = {
    xMin: 300,
    xMax: 800,
    yMin: Math.min(...data.map(i => Math.min(...i.absorbance.filter(i => i.wavelength > 300).map(i => i.absorbance)))) || 0,
    yMax: Math.max(...data.map(i => Math.max(...i.absorbance.filter(i => i.wavelength > 300).map(i => i.absorbance))) || 0.5),
  }

  const colorbarProps = {
    numStops: 8,
    width: 20,
    stopHeight: 10,
    height: height - margin.bottom,
  }
  // const limits = { xLeft: 300, xRight: 800, yBottom: 0, yTop: 0.5 }


  const zeroEightHundred = (data) => { // absorbance data
    const a800 = data[data.findIndex(item => item.wavelength === 800)].absorbance
    return data.map(item => ({ ...item, absorbance: item.absorbance - a800 }))
  }

  const hasData = Array.isArray(data) && data.length > 0 && !data.every(item => typeof item === 'undefined');

  useEffect(() => {
    const svg = d3.select(svgRef.current)
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .style("background-color", responsePlotColors.bg);

    const g = svg.select("g").remove();
    const newG = svg.append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xScale = d3.scaleLinear()
      .domain([limits.xMin, limits.xMax])
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain([limits.yMin * 1.1, limits.yMax * 1.1])
      .range([height, 0]);

    newG.append('g')
      .attr('transform', `translate(0, ${height})`)
      .call(d3.axisBottom(xScale));

    newG.append('g')
      .call(d3.axisLeft(yScale));

    newG.selectAll(".y-label")
      .data(["Absorbance"])
      .join(
        enter => enter.append("text")
          .attr("class", "y-label")
          .attr("transform", `rotate(-90), translate(${- height / 2}, ${-0.9 * margin.left})`)
          .attr("dy", "1em")
          .style("text-anchor", "middle")
          .style("fill", responsePlotColors.fg)
          .text(d => d),
        update => update.text(d => d),
        exit => exit.remove()
      );

    newG.selectAll(".x-label")
      .data(["Wavelength (nm)"])
      .join(
        enter => enter
          .append("text")
          .attr("class", "x-label")
          .attr("transform", `translate(${width / 2}, ${height + (0.8 * margin.bottom)})`)
          .style("fill", responsePlotColors.fg)
          .style("text-anchor", "middle")
          .text(d => d),
        update => update.text(d => d),
        exit => exit.remove()
      );

    if (hasData) {
      const allAbsorbanceData = data.map(trace => zeroEightHundred(trace.absorbance))

      const concs = [...new Set(data.map(item => item.compound_concentration))]

      if (allAbsorbanceData.length === 0) return;


      const line = d3.line()
        .x(d => xScale(d.wavelength))
        .y(d => yScale(d.absorbance));

      // Plot absorbance for each test well
      allAbsorbanceData.forEach((absorbanceMeasurement, idx) => {

        const exclude = excludeDict[data[idx].compound_concentration]
        if (absorbanceMeasurement.length > 0) {
          newG.append('path')
            .datum(absorbanceMeasurement.filter(item => item.wavelength > limits.xMin && item.wavelength <= limits.xMax))
            .attr("d", line)
            .attr("class", "line")
            .attr("fill", "none")
            .attr("stroke",  infernoScale(data[idx].compound_concentration / Math.max(...concs)))
            // .attr("stroke", excludeDict[data[idx].compound_concentration] ? "#FFFFFF" : infernoScale(data[idx].compound_concentration / Math.max(...concs)))
            .attr("stroke-width", 3)
            .attr("stroke-linejoin", "round")
            .attr("stroke-linecap", "round")
            .style("stroke-dasharray", exclude ? (6,6): "")
            // .style("stroke", i => (exclude ? "solid" : "dashed"))
        }
      });

      const colorbar = newG.append("g")
        .classed("cbar", true)
        .attr("transform", `translate(${width - margin.left}, ${margin.top})`) // Position the colorbar


      const barHeight = colorbarProps.height / colorbarProps.numStops

      colorbar.selectAll('rect')
        .data(concs)
        .join("rect")
        .attr("x", 0)
        .attr("y", (i, idx) => (colorbarProps.height / colorbarProps.numStops) * idx)
        .attr('fill', i => (i.exclude ? responsePlotColors.bg : infernoScale(i / Math.max(...concs))))
        .attr('height', barHeight)
        .attr('width', colorbarProps.width)
      // .join('text')

      colorbar.selectAll('text')
        .data(concs)
        .join('text')
        .attr('x', colorbarProps.width + 5) // Position text to the right of the rectangles
        // .attr('y', (i) => (i + 1) * (colorbarProps.height / colorbarProps.numStops)) // Vertically center text
        .attr("y", (i, idx) => (idx + 1) * barHeight - (barHeight / 2))
        .style('alignment-baseline', 'middle')
        .style('fill', responsePlotColors.fg)
        .style('font-size', '0.8em')
        .text(i => `${i.toFixed(2)}`);

      colorbar.append('text')
        .attr('y', -10)
        .text('[Ligand] μM')
        .style('fill', responsePlotColors.fg)
    }

  }, [data]);

  return (
    <>
      <svg ref={svgRef}>
        <g className="plot-area" />
      </svg>
    </>
  );
}

AbsorbancePlotMultiple.propTypes = {
  data: PropTypes.shape({
    test_wells: PropTypes.arrayOf(
      PropTypes.shape({
        absorbance: PropTypes.arrayOf(
          PropTypes.shape({
            wavelength: PropTypes.number,
            absorbance: PropTypes.number,
          })
        ),
      })
    ),
  }),
};
