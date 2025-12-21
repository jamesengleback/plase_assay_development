import { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';
import PropTypes from 'prop-types';
import { responsePlotColors } from '../Absorbance/colors.jsx';

export default function ResponsePlot(props) {
  const svgRef = useRef();
  const margin = { top: 20, right: 30, bottom: 60, left: 120 };
  const [dimensions, setDimensions] = useState({
    width: (window.innerWidth * 0.8) - margin.left - margin.right,
    height: 500 - margin.top - margin.bottom
  });

  useEffect(() => {
    const handleResize = () => {
      setDimensions({
        width: (window.innerWidth * 0.8) - margin.left - margin.right,
        height: 500 - margin.top - margin.bottom
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const { width, height } = dimensions;
  const data = props.dose_response;

  const getConc = (d) => {
    const val = typeof d.concentration === 'object' ? d.concentration.parsedValue : d.concentration;
    return parseFloat(val);
  };
  const getResp = (d) => {
    const val = typeof d.response === 'object' ? d.response.parsedValue : d.response;
    return parseFloat(val);
  };
  const getKm = () => {
    const val = typeof props.km === 'object' ? props.km.parsedValue : props.km;
    return parseFloat(val);
  };
  const mm_curve = (x, vmax, km) => (parseFloat(vmax) * x) / (parseFloat(km) + x);

  useEffect(() => {
    console.log('ResponsePlot useEffect triggered');
    console.log('data:', data);
    console.log('props.vmax:', props.vmax);
    console.log('props.km:', props.km);
    if (data) {
      console.log('Data is present, proceeding with D3');

      console.log('Processing data...');
      const concentrations = data.map(i => getConc(i));
      const responses = data.map(i => getResp(i));
      console.log('concentrations:', concentrations);
      console.log('responses:', responses);

      const cMax = Math.max(...concentrations);
      console.log('cMax:', cMax);
      const x = Array.from({ length: cMax }, (val, idx) => idx);
      const y_pred = (props.vmax && getKm()) ? x.map(x_i => ({
        concentration: x_i,
        response: mm_curve(x_i, props.vmax, getKm())
      })) : [];
      console.log('x:', x);
      console.log('y_pred:', y_pred);

      const svg = d3.select(svgRef.current);
      svg.attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .attr("viewBox", `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
        .style("background-color", responsePlotColors.bg);

      // Clear existing elements to ensure clean re-render
      svg.selectAll("*").remove();

      // Always append the g element and sub-elements
      const g = svg.append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);
      g.append('g').attr('class', 'x-axis');
      g.append('g').attr('class', 'y-axis');
      g.append('path').attr('class', 'line');
      g.append('path').attr('class', 'mm-line');
      g.append('path').attr('class', 'kd-line-vertical');
      g.append('path').attr('class', 'kd-line-horizontal');
      g.append('g').attr('class', 'dots');
      g.append('text').attr('class', 'y-label');
      g.append('text').attr('class', 'x-label');

      const xScale = d3.scaleLinear()
        .domain([0, Math.max(d3.max(data, d => getConc(d)), 0.1)])
        .range([0, width]);

      const maxResponse = Math.max(...data.map(item => parseFloat(item.response)));
      const minResponse = Math.min(...data.map(item => parseFloat(item.response)));
      const dataRange = maxResponse - minResponse;
      const padding = Math.max(dataRange * 0.05, 0.01); // 5% padding or at least 0.01

      let yMin = 0;
      let yMax = Math.max(maxResponse + padding, props.vmax ? parseFloat(props.vmax) * 1.05 : maxResponse + padding);

      // Ensure yMax is at least a bit above yMin
      if (yMax <= yMin) yMax = yMin + 0.1;

      // If vmax is much higher, adjust
      if (props.vmax && parseFloat(props.vmax) > yMax) {
        yMax = parseFloat(props.vmax) * 1.05;
      }
      const yScale = d3.scaleLinear()
        .domain([yMax, yMin])
        .range([0, height]);

      console.log('xScale domain:', xScale.domain());
      console.log('yScale domain:', yScale.domain());
      console.log('yMax:', yMax, 'yMin:', yMin);

      const xAxis = g.select('.x-axis') // Select and update the x-axis
        .attr('transform', `translate(0, ${height})`)
        .call(d3.axisBottom(xScale));

      xAxis.selectAll('text').style('fill', responsePlotColors.fg).style('font-size', '12px');
      xAxis.selectAll('line').style('stroke', responsePlotColors.fg);
      xAxis.select('path').style('stroke', responsePlotColors.fg);

      const yAxis = g.select('.y-axis') // Select and update the y-axis
        .call(d3.axisLeft(yScale));

      yAxis.selectAll('text').style('fill', responsePlotColors.fg).style('font-size', '12px');
      yAxis.selectAll('line').style('stroke', responsePlotColors.fg);
      yAxis.select('path').style('stroke', responsePlotColors.fg);

      g.selectAll(".y-label")
        .attr("transform", `translate(${-60}, ${height / 2}), rotate(-90)`)
        .data(["Response"])
        .style("fill", responsePlotColors.fg)
        .style("font-size", "14px")
        .join(
          enter => enter.append("text")
            .attr("class", "y-label")
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .text(d => d),
          update => update.text(d => d),
          exit => exit.remove()
        );

      g.selectAll(".title")
        .data([props.title])
        .join(
          enter => {
            const textElement = enter.append("text")
              .attr("class", "title")
              .attr("x", width / 2)
              .attr("y", props.title && props.title.length > 60 ? 2 : 5)
              .style("text-anchor", "middle")
              .style("fill", responsePlotColors.fg)
              .style("font-size", props.title && props.title.length > 50 ? "12px" : "14px")
              .style("font-weight", "bold");
            
            if (props.title && props.title.length > 60) {
              const mid = props.title.lastIndexOf(' ', 30);
              const line1 = props.title.substring(0, mid);
              const line2 = props.title.substring(mid + 1);
              textElement.append("tspan")
                .attr("x", width / 2)
                .attr("dy", "0")
                .text(line1);
              textElement.append("tspan")
                .attr("x", width / 2)
                .attr("dy", "1.2em")
                .text(line2);
            } else {
              textElement.text(d => d);
            }
            return textElement;
          },
          update => {
            update.each(function(d) {
              const textElement = d3.select(this);
              textElement.selectAll("tspan").remove(); // Clear existing tspans
              textElement.attr("y", d && d.length > 60 ? 2 : 5)
                .style("font-size", d && d.length > 50 ? "12px" : "14px");
              
              if (d && d.length > 60) {
                const mid = d.lastIndexOf(' ', 30);
                const line1 = d.substring(0, mid);
                const line2 = d.substring(mid + 1);
                textElement.append("tspan")
                  .attr("x", width / 2)
                  .attr("dy", "0")
                  .text(line1);
                textElement.append("tspan")
                  .attr("x", width / 2)
                  .attr("dy", "1.2em")
                  .text(line2);
              } else {
                textElement.text(d);
              }
            });
            return update;
          },
          exit => exit.remove()
        );

      g.selectAll(".x-label")
        .data(["Concentration"])
        .style("fill", responsePlotColors.fg)
        .style("font-size", "14px")
        .attr("transform", `translate(${width / 3}, ${height + margin.top + (margin.bottom / 2)})`)
        .join(
          enter => enter
            .append("text")
            .attr("class", "x-label")
            .style("text-anchor", "middle")
            .text(d => d),
          update => update.text(d => d),
          exit => exit.remove()
        );

      // g.select('.line') // Select and update the data for the experimental data line
      //   .datum(data.filter(d => !d.exclude))
      //   .attr("fill", "none")
      //   .attr("stroke", responsePlotColors.line)
      //   .attr("stroke-width", 1.5)
      //   .attr("stroke-linejoin", "round")
      //   .attr("stroke-linecap", "round")
      //   .attr("d", line);

      const dots = g.select('.dots')
        .selectAll('.dot')
        .data(data, d => getConc(d));

      dots.join(
        enter => enter.append('circle')
          .attr('class', 'dot')
          .attr('cx', d => xScale(getConc(d)))
          .attr('cy', d => yScale(d.response))
          .attr('r', 5)
          .style('fill', d => d.exclude ? responsePlotColors.dotExclude : responsePlotColors.dot),
        update => update.transition()
          .duration(100)
          .attr('cx', d => xScale(getConc(d)))
          .attr('cy', d => yScale(d.response))
          .style('fill', d => d.exclude ? responsePlotColors.dotExclude : responsePlotColors.dot),
        exit => exit.remove()
      );

      // Add stats box
      const stats = g.append('g').attr('class', 'stats');
      stats.append('rect')
        .attr('x', width - 200)
        .attr('y', 50)
        .attr('width', 180)
        .attr('height', 80)
        .style('fill', 'var(--gruv-2)')
        .style('stroke', responsePlotColors.fg)
        .style('stroke-width', 1);
      stats.append('text')
        .attr('x', width - 190)
        .attr('y', 70)
        .style('fill', 'var(--fg)')
        .style('font-size', '12px')
        .text(`Km: ${getKm() ? getKm().toFixed(2) : 'N/A'}`);
      stats.append('text')
        .attr('x', width - 190)
        .attr('y', 90)
        .style('fill', 'var(--fg)')
        .style('font-size', '12px')
        .text(`Vmax: ${props.vmax ? parseFloat(props.vmax).toFixed(2) : 'N/A'}`);
      stats.append('text')
        .attr('x', width - 190)
        .attr('y', 110)
        .style('fill', 'var(--fg)')
        .style('font-size', '12px')
        .text(`R²: ${props.r_squared ? parseFloat(props.r_squared).toFixed(3) : 'N/A'}`);

      const y_predLine = d3.line()
        .x(d => xScale(d.concentration))
        .y(d => yScale(d.response));

      if (y_pred.length > 0) {
        g.select('.mm-line') // Select and update the Michaelis-Menten curve
          .datum(y_pred)
          .attr("fill", "none")
          .attr("stroke", responsePlotColors.line)
          .attr("stroke-width", 1.5)
          .attr("stroke-linejoin", "round")
          .attr("stroke-linecap", "round")
          .attr("d", y_predLine);
      }

      // kd annotation (vertical line)
      if (getKm()) {
        const kd_line_vertical = d3.line()
          .x(() => xScale(getKm()))
          .y(d => yScale(d));

        g.select('.kd-line-vertical')
          .datum([0, parseFloat(props.vmax)])
          .attr("d", kd_line_vertical)
          .attr("fill", "none")
          .attr("stroke", "grey")
          .style("stroke-dasharray", ("3, 3"))
          .attr("stroke-width", 1.5)
          .attr("stroke-linejoin", "round")
          .attr("stroke-linecap", "round");
      }

      // vmax annotation (horizontal line)
      if (props.vmax) {
        const vmax_line = d3.line()
          .x(d => xScale(d))
          .y(() => yScale(parseFloat(props.vmax)));

        g.select('.kd-line-horizontal')
          .datum([0, Math.max(...x)])
          .attr("d", vmax_line)
          .attr("fill", "none")
          .attr("stroke", "grey")
          .style("stroke-dasharray", ("3, 3"))
          .attr("stroke-width", 1.5)
          .attr("stroke-linejoin", "round")
          .attr("stroke-linecap", "round");
      }

      console.log('ResponsePlot useEffect completed successfully');
    } else {
      console.log('No data available, skipping D3 operations');
    }
  }, [data, props.vmax, props.km, width, height]); // Ensure dependencies are correct

  return (
    <>
      <svg ref={svgRef} style={{ border: '1px solid var(--fg)' }}></svg>
    </>
  );
}


ResponsePlot.propTypes = {
  dose_response: PropTypes.arrayOf(
    PropTypes.shape({
      concentration: PropTypes.number.isRequired,
      response: PropTypes.number.isRequired,
      exclude: PropTypes.bool,
    })
  ).isRequired,
  vmax: PropTypes.number.isRequired,
  km: PropTypes.number.isRequired,
  title: PropTypes.string,
  r_squared: PropTypes.number,
};


// import { useRef, useEffect } from 'react';
// import * as d3 from 'd3';
// import PropTypes from 'prop-types';
//
// export default function ResponsePlot(props) {
//   const svgRef = useRef();
//   const margin = { top: 20, right: 30, bottom: 35, left: 50 };
//   const width = 400 - margin.left - margin.right;
//   const height = 200 - margin.top - margin.bottom;
//   const data = props.dose_response
//
//   const mm_curve = (x, vmax, km) => (vmax * x) / (km + x)
//
//
//   useEffect(() => {
//     console.warn(data)
//
//     const x = Array.from({ length: 501 }, (val, idx) => idx)
//     const y_pred = x.map(x_i => ({
//       concentration: x_i,
//       response: mm_curve(x_i, props.vmax, props.km)
//     }))
//
//     const svg = d3.select(svgRef.current)
//       .attr("width", width + margin.left + margin.right)
//       .attr("height", height + margin.top + margin.bottom)
//       .style("background-color", '#eee');
//
//     const g = svg.append("g")
//       .attr("transform", `translate(${margin.left}, ${margin.top})`);
//
//     if (data) {
//
//       const xScale = d3.scaleLinear()
//         .domain([0, d3.max(data, d => d.concentration)])
//         .range([0, width]);
//
//       const yScale = d3.scaleLinear()
//         .domain([Math.max(
//           props.vmax * 1.1,
//           Math.max(...data.map(item => item.response)) * 1.1
//         ), 0])
//         .range([0, height]);
//
//       g.append('g')
//         .attr('transform', `translate(0, ${height})`) // Translate the x-axis within the 'g'
//         .call(d3.axisBottom(xScale));
//
//       g.append('g')
//         .call(d3.axisLeft(yScale));
//
//       g.selectAll(".y-label")
//         .data(["Response"])
//         .join(
//           enter => enter.append("text")
//             .attr("class", "y-label")
//             .attr("transform", "rotate(-90)")
//             .attr("y", 0 - margin.left)
//             .attr("x", 0 - (height / 2))
//             .attr("dy", "1em")
//             .style("text-anchor", "middle")
//             .text(d => d),
//           update => update.text(d => d),
//           exit => exit.remove()
//         );
//
//       g.selectAll(".x-label")
//         .data(["Concentration"])
//         .join(
//           enter => enter
//             .append("text")
//             .attr("class", "x-label")
//             .attr("transform", `translate(${width / 2}, ${height + margin.bottom})`)
//             .style("text-anchor", "middle")
//             .text(d => d),
//           update => update.text(d => d),
//           exit => exit.remove()
//         );
//
//       const line = d3.line()
//         .x(d => xScale(d.concentration))
//         .y(d => yScale(d.response));
//
//       // g.select('.line')
//       //   .remove()
//
//       g.append('path')
//         .attr("class", "line")
//         .attr("fill", "none")
//         .attr("stroke", "steelblue")
//         .attr("stroke-width", 1.5)
//         .attr("stroke-linejoin", "round")
//         .attr("stroke-linecap", "round");
//
//       g.select('.line')
//         .remove()
//         .datum(data.filter(d => !d.exclude))
//         .attr("d", line)
//
//       g.selectAll('.dot')
//         .data(data, d => d.concentration)
//         .join(
//           enter => enter.append('circle')
//             .attr('class', 'dot')
//             .attr('cx', d => xScale(d.concentration))
//             .attr('cy', d => yScale(d.response))
//             .attr('r', 5) // Radius of the circles
//             .style('fill', d => d.exclude ? '#ebdbb2' : 'steelblue'),
//           update => update.transition()
//             .duration(100)
//             .style('fill', d => d.exclude ? '#ebdbb2' : 'steelblue'),
//           exit => exit.remove()
//         )
//
//       const y_predLine = d3.line()
//         .x(d => xScale(d.concentration))
//         .y(d => yScale(d.response))
//
//       g.append('path')
//         .datum(y_pred)
//         .attr("d", y_predLine)
//         .attr("class", "mm-line")
//         .attr("fill", "none")
//         .attr("stroke", "orange")
//         .attr("stroke-width", 1.5)
//         .attr("stroke-linejoin", "round")
//         .attr("stroke-linecap", "round");
//
//       // g.select('.mm-line')
//
//       // kd annotation
//       const kd_line = d3.line()
//         .x(d => xScale(props.km))
//         .y(d => yScale(d));
//
//       g.append('path')
//         .datum([0, props.vmax])
//         .attr("d", kd_line)
//         .attr("class", "kd-line")
//         .attr("fill", "none")
//         .attr("stroke", "grey")
//         .style("stroke-dasharray", ("3, 3"))  // <== This line here!!
//         .attr("stroke-width", 1.5)
//         .attr("stroke-linejoin", "round")
//         .attr("stroke-linecap", "round");
//
//       // vmax annotation
//       const vmax_line = d3.line()
//         .x(d => xScale(d))
//         .y(d => yScale(props.vmax));
//
//       g.append('path')
//         .datum([0, Math.max(...x)])
//         .attr("d", vmax_line)
//         .attr("class", "kd-line")
//         .attr("fill", "none")
//         .attr("stroke", "grey")
//         .style("stroke-dasharray", ("3, 3"))  // <== This line here!!
//         .attr("stroke-width", 1.5)
//         .attr("stroke-linejoin", "round")
//         .attr("stroke-linecap", "round");
//
//     }
//   }, [data])
//   return (
//     <svg ref={svgRef}></svg>
//   )
// }
