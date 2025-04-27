import React, { useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import * as d3 from 'd3';
import infernoScale, { responsePlotColors } from './colors.jsx';

export default function AbsorbancePlotMultiple({ data }) {
  const svgRef = useRef();
  const margin = { top: 20, right: 30, bottom: 45, left: 60 };
  const width = 800 - margin.left - margin.right;
  const height = 400 - margin.top - margin.bottom;
  const limits = { xLeft: 300, xRight: 800, yBottom: 0, yTop: 0.5 }
  //const colorScale = d3.scaleOrdinal(d3.schemeCategory10);
  const colorScale = d3.interpolateRgb("purple", "orange")

  const zeroEightHundred = (data) => { // absorbance data
    const a800 = data[data.findIndex(item => item.wavelength === 800)].absorbance
    return data.map(item => ({ ...item, absorbance: item.absorbance - a800 }))
  }

  useEffect(() => {
    const hasData = Array.isArray(data) && data.length > 0;
    // console.warn(hasData)
    // console.warn('data: ', data)

    if (hasData) {
      const svg = d3.select(svgRef.current)
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .style("background-color", responsePlotColors.bg);

      const g = svg.select("g").remove();
      const newG = svg.append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

      // Extract all absorbance data for scaling
      // console.warn(data)
      const allAbsorbanceData = data.map(trace => zeroEightHundred(trace.absorbance))
      //const allAbsorbanceData = data.map(well => well.absorbance.map(
      //  item => {
      //    return (
      //      {
      //        ...item,
      //        absobance: item.absorbance - well.absorbance[well.absorbance.length - 1]
      //      }
      //    )
      //  }
      //)
      //)

      if (allAbsorbanceData.length === 0) return;

      const xScale = d3.scaleLinear()
        .domain([300, 800])
        .range([0, width]);

      const yScale = d3.scaleLinear()
        .domain([0, 0.5]) // Adjust y-domain based on data
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
            .attr("transform", `rotate(-90), translate(${- height/2}, ${-0.9 * margin.left})`)
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

      const line = d3.line()
        .x(d => xScale(d.wavelength))
        .y(d => yScale(d.absorbance));

      // Plot absorbance for each test well
      allAbsorbanceData.forEach((absorbanceMeasurement, idx) => {

        // console.warn(absorbanceMeasurement);
        if (absorbanceMeasurement.length > 0) {
          newG.append('path')
            .datum(absorbanceMeasurement.filter(item => item.wavelength > limits.xLeft && item.wavelength <= limits.xRight))
            .attr("d", line)
            .attr("class", "line")
            .attr("fill", "none")
            .attr("stroke", infernoScale(data[idx].compound_concentration / 500))
            .attr("stroke-width", 3)
            .attr("stroke-linejoin", "round")
            .attr("stroke-linecap", "round");
        }
      });

      const colorbarProps = {
        numStops: 8,
        width: 20,
        stopHeight: 10,
        height: height - margin.bottom,
      }

      const colorbar = newG.append("g")
        .classed("cbar", true)
        .attr("transform", `translate(${width - margin.left}, ${margin.top})`) // Position the colorbar

      colorbar.selectAll('rect')
        .data(d3.range(colorbarProps.numStops))
        .join("rect")
        .attr("x", 0)
        .attr("y", (i) => (colorbarProps.height / colorbarProps.numStops) * i)
        .attr('fill', i => infernoScale(data[i].compound_concentration / 500))
        .attr('height', (colorbarProps.height / colorbarProps.numStops))
        .attr('width', colorbarProps.width)
        .join('text')

      colorbar.selectAll('text')
        .data(d3.range(colorbarProps.numStops))
        .join('text')
        .attr('x', colorbarProps.width + 5) // Position text to the right of the rectangles
        .attr('y', (i) => (i + 1) * (colorbarProps.height / colorbarProps.numStops)) // Vertically center text
        .style('alignment-baseline', 'middle')
        .style('fill', responsePlotColors.fg)
        .style('font-size', '0.8em')
        .text(i => `${(data[i].compound_concentration).toFixed(0)}`);

      colorbar.append('text')
        .attr('y', -10)
        .text('μM')
        .style('fill', responsePlotColors.fg)

      //.attr("height", height * 0.8)
      //.attr("width", 20)

      //.data(d3.range(numStops))
      //  .join("rect")
      //    .attr("y", (i) => yScale(i / (numStops - 1) * (d3.extent(allAbsorbanceData.flat(), d => d.absorbance)[1] || 0.5))) // Approximate y-position
      //    .attr("height", Math.max(0, height / numStops))
      //    .attr("fill", (i) => colorScaleForBar(i / (numStops - 1)));

      // Add Colorbar
      //const colorbarWidth = 20;
      //const colorbarHeight = height;
      //const numStops = 10; // Number of color stops in the bar
      //
      //const colorScaleForBar = d3.scaleLinear()
      //  .domain([0, 1]) // Normalized concentration (assuming 0 to 500 uM)
      //  .range(["purple", "orange"]);
      //
      //const colorbar = newG.append("g")
      //  .attr("transform", `translate(${width + 30}, 0)`); // Position the colorbar
      //
      //colorbar.selectAll("rect")
      //  .data(d3.range(numStops))
      //  .join("rect")
      //  .attr("y", (i) => yScale(i / (numStops - 1) * (d3.extent(allAbsorbanceData.flat(), d => d.absorbance)[1] || 0.5))) // Approximate y-position
      //  .attr("height", Math.max(0, height / numStops))
      //  .attr("width", colorbarWidth)
      //  .attr("fill", (i) => colorScaleForBar(i / (numStops - 1)));
      //
      //const colorbarAxisScale = d3.scaleLinear()
      //  .domain([0, 500]) // Actual concentration range
      //  .range([height, 0]);
      //
      //const colorbarAxis = d3.axisRight(colorbarAxisScale)
      //  .ticks(5);
      //
      //colorbar.append("g")
      //  .attr("transform", `translate(${colorbarWidth}, 0)`)
      //  .call(colorbarAxis);
      //
      //colorbar.append("text")
      //  .attr("x", colorbarWidth + 10)
      //  .attr("y", -10)
      //  .style("text-anchor", "start")
      //  .text("Compound Concentration (uM)");
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
