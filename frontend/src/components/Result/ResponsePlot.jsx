import { useRef, useEffect } from 'react';
import * as d3 from 'd3';
import PropTypes from 'prop-types';
import { responsePlotColors } from '../Absorbance/colors.jsx';

export default function ResponsePlot(props) {
  const svgRef = useRef();
  const margin = { top: 20, right: 30, bottom: 35, left: 60 };
  const width = 600 - margin.left - margin.right;
  const height = 300 - margin.top - margin.bottom;
  const data = props.dose_response;

  const mm_curve = (x, vmax, km) => (vmax * x) / (km + x);

  useEffect(() => {
    if (data) {

      const x = Array.from({ length: 501 }, (val, idx) => idx);
      const y_pred = x.map(x_i => ({
        concentration: x_i,
        response: mm_curve(x_i, props.vmax, props.km)
      }));

      const svg = d3.select(svgRef.current)
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .style("background-color", responsePlotColors.bg);

      const g = svg.select("g") // Select the existing 'g' element
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

      // If the 'g' element doesn't exist yet, create it
      if (g.empty()) {
        const gEnter = svg.append("g")
          .attr("transform", `translate(${margin.left}, ${margin.top})`);
        gEnter.append('g').attr('class', 'x-axis');
        gEnter.append('g').attr('class', 'y-axis');
        gEnter.append('path').attr('class', 'line');
        gEnter.append('path').attr('class', 'mm-line');
        gEnter.append('path').attr('class', 'kd-line-vertical');
        gEnter.append('path').attr('class', 'kd-line-horizontal');
        gEnter.append('g').attr('class', 'dots');
        gEnter.append('text').attr('class', 'y-label');
        gEnter.append('text').attr('class', 'x-label');
      }

      const xScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.concentration)])
        .range([0, width]);

      const yScale = d3.scaleLinear()
        .domain([Math.max(
          props.vmax * 1.1,
          Math.max(...data.map(item => item.response)) * 1.1
        ), 0])
        .range([0, height]);

      g.select('.x-axis') // Select and update the x-axis
        .attr('transform', `translate(0, ${height})`)
        .call(d3.axisBottom(xScale));

      g.select('.y-axis') // Select and update the y-axis
        .call(d3.axisLeft(yScale));

      g.selectAll(".y-label")
        .attr("transform", `translate(${- (0.7 * margin.left)}, ${0.8 * height}), rotate(-90)`)
        .data(["Response"])
        .style("fill", responsePlotColors.fg)
        .join(
          enter => enter.append("text")
            .attr("class", "y-label")
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .text(d => d),
          update => update.text(d => d),
          exit => exit.remove()
        );

      g.selectAll(".x-label")
        .data(["Concentration"])
        .style("fill", responsePlotColors.fg)
        .attr("transform", `translate(${width / 3}, ${height + margin.top + (margin.bottom / 3)})`)
        .join(
          enter => enter
            .append("text")
            .attr("class", "x-label")
            .style("text-anchor", "middle")
            .text(d => d),
          update => update.text(d => d),
          exit => exit.remove()
        );

      const line = d3.line()
        .x(d => xScale(d.concentration))
        .y(d => yScale(d.response));

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
        .data(data, d => d.concentration);

      dots.join(
        enter => enter.append('circle')
          .attr('class', 'dot')
          .attr('cx', d => xScale(d.concentration))
          .attr('cy', d => yScale(d.response))
          .attr('r', 5)
          .style('fill', d => d.exclude ? responsePlotColors.dotExclude : responsePlotColors.dot),
        update => update.transition()
          .duration(100)
          .attr('cx', d => xScale(d.concentration))
          .attr('cy', d => yScale(d.response))
          .style('fill', d => d.exclude ? responsePlotColors.dotExclude : responsePlotColors.dot),
        exit => exit.remove()
      );

      const y_predLine = d3.line()
        .x(d => xScale(d.concentration))
        .y(d => yScale(d.response));

      g.select('.mm-line') // Select and update the Michaelis-Menten curve
        .datum(y_pred)
        .attr("fill", "none")
        .attr("stroke", responsePlotColors.line)
        .attr("stroke-width", 1.5)
        .attr("stroke-linejoin", "round")
        .attr("stroke-linecap", "round")
        .attr("d", y_predLine);

      // kd annotation (vertical line)
      const kd_line_vertical = d3.line()
        .x(d => xScale(props.km))
        .y(d => yScale(d));

      g.select('.kd-line-vertical')
        .datum([0, props.vmax])
        .attr("d", kd_line_vertical)
        .attr("fill", "none")
        .attr("stroke", "grey")
        .style("stroke-dasharray", ("3, 3"))
        .attr("stroke-width", 1.5)
        .attr("stroke-linejoin", "round")
        .attr("stroke-linecap", "round");

      // vmax annotation (horizontal line)
      const vmax_line = d3.line()
        .x(d => xScale(d))
        .y(d => yScale(props.vmax));

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
  }, [data, props.vmax, props.km]); // Ensure dependencies are correct

  return (
    <svg ref={svgRef}></svg>
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
