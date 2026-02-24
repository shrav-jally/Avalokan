import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import cloud from 'd3-cloud';

const SentimentWordCloud = ({ words, sentiment }) => {
    const containerRef = useRef(null);
    const svgRef = useRef(null);

    // Define color scales based on sentiment
    const colorScales = {
        positive: d3.scaleSequential(d3.interpolateGreens).domain([0, 100]),
        neutral: d3.scaleSequential(d3.interpolateGreys).domain([0, 100]),
        negative: d3.scaleSequential(d3.interpolateReds).domain([0, 100]),
    };

    const colorScale = colorScales[sentiment] || colorScales.neutral;

    useEffect(() => {
        if (!containerRef.current || !words || words.length === 0) return;

        // Dimensions
        const width = containerRef.current.clientWidth || 500;
        const height = containerRef.current.clientHeight || 300;

        // Clear previous SVG
        d3.select(containerRef.current).selectAll('svg').remove();

        // Create SVG container
        const svg = d3.select(containerRef.current)
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        const g = svg.append('g')
            .attr('transform', `translate(${width / 2},${height / 2})`);

        svgRef.current = g;

        // Tooltip setup
        const tooltip = d3.select(containerRef.current)
            .append('div')
            .attr('class', 'word-cloud-tooltip')
            .style('position', 'absolute')
            .style('visibility', 'hidden')
            .style('background', 'rgba(0, 0, 0, 0.8)')
            .style('color', '#fff')
            .style('padding', '5px 10px')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .style('z-index', '10');

        // Setup Scale for font sizes
        const sizeScale = d3.scaleLinear()
            .domain([d3.min(words, d => d.value) || 0, d3.max(words, d => d.value) || 1])
            .range([15, 80]); // Min 15px, Max 80px

        // Layout configuration
        const layout = cloud()
            .size([width, height])
            .words(words.map(d => Object.create(d)))
            .padding(5)
            .rotate(() => (~~(Math.random() * 2) * 90) - 45) // Randomize between -45 and 45 degrees via step
            .font('Impact')
            .fontSize(d => sizeScale(d.value))
            .on('end', draw);

        layout.start();

        // Draw function
        function draw(drawnWords) {
            const texts = g.selectAll('text')
                .data(drawnWords, d => d.text);

            // EXIT
            texts.exit()
                .transition()
                .duration(500)
                .style('opacity', 0)
                .remove();

            // ENTER
            const enterTexts = texts.enter()
                .append('text')
                .style('font-size', '1px') // Start small
                .style('font-family', 'Impact')
                .style('fill', d => colorScale(d.value))
                .attr('text-anchor', 'middle')
                .attr('transform', `translate(0,0) rotate(0)`)
                .text(d => d.text)
                .on('mouseover', (event, d) => {
                    tooltip.text(`${d.text}: ${d.value}`)
                        .style('visibility', 'visible');
                    d3.select(event.currentTarget).style('opacity', 0.8);
                })
                .on('mousemove', (event) => {
                    // Get coordinates relative to the parent container
                    const [x, y] = d3.pointer(event, containerRef.current);
                    tooltip.style('top', `${y - 30}px`)
                        .style('left', `${x + 10}px`);
                })
                .on('mouseout', (event) => {
                    tooltip.style('visibility', 'hidden');
                    d3.select(event.currentTarget).style('opacity', 1);
                });

            // UPDATE + ENTER (Merge)
            enterTexts.merge(texts)
                .transition()
                .duration(800)
                .style('font-size', d => `${d.size}px`)
                .style('fill', d => colorScale(d.value)) // Update color
                .attr('transform', d => `translate(${d.x},${d.y}) rotate(${d.rotate})`);
        }

        // Cleanup
        return () => {
            d3.select(containerRef.current).selectAll('.word-cloud-tooltip').remove();
            // d3-cloud doesn't have a built in stop/destroy for the interval if interrupted mid-layout,
            // but layout.stop() is available in newer versions if it runs asynchronously.
            if (layout.stop) layout.stop();
        };

    }, [words, sentiment, colorScale]);

    return (
        <div
            ref={containerRef}
            style={{ width: '100%', height: '100%', position: 'relative' }}
        />
    );
};

export default SentimentWordCloud;
