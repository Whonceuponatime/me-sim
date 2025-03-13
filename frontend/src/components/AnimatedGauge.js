import React, { useState, useRef, useEffect, memo, useMemo } from 'react';
import { Box } from '@mui/material';
import GaugeChart from 'react-gauge-chart';

const GAUGE_SIZE = 200;

const AnimatedGauge = memo(({ id, value, normalizedValue, label, formatValue, colors, ...props }) => {
  const [animatedValue, setAnimatedValue] = useState(normalizedValue);
  const animationRef = useRef(null);
  const velocityRef = useRef(0);
  const prevValueRef = useRef(normalizedValue);

  // Fixed container style with absolute dimensions
  const containerStyle = useMemo(() => ({
    width: GAUGE_SIZE,
    height: GAUGE_SIZE,
    position: 'relative',
    margin: '0 auto',
    '& > div': {
      width: `${GAUGE_SIZE}px !important`,
      height: `${GAUGE_SIZE}px !important`,
      position: 'absolute !important',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      '& svg': {
        width: `${GAUGE_SIZE}px !important`,
        height: `${GAUGE_SIZE}px !important`,
        position: 'absolute !important',
        left: 0,
        top: 0,
        willChange: 'transform'
      }
    }
  }), []);

  // Memoize chart props
  const chartProps = useMemo(() => ({
    id,
    nrOfLevels: 20,
    colors,
    arcWidth: 0.3,
    textColor: props.textColor || "#ffffff",
    needleColor: props.needleColor || "#ffffff",
    needleBaseColor: props.needleColor || "#ffffff",
    cornerRadius: 3,
    marginInPercent: 0.02,
    animate: false
  }), [id, colors, props.textColor, props.needleColor]);

  useEffect(() => {
    const targetValue = normalizedValue;
    const currentValue = prevValueRef.current;

    // Reset animation if it's running
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }

    // Spring animation parameters
    const stiffness = 0.025; // Lower = more gradual movement
    const damping = 0.75;    // Higher = less oscillation
    const mass = 1;          // Higher = more inertia

    let velocity = velocityRef.current;
    let position = currentValue;

    const animate = () => {
      // Calculate spring force
      const displacement = targetValue - position;
      const springForce = displacement * stiffness;
      
      // Apply forces and update velocity
      const dampingForce = -velocity * damping;
      const acceleration = (springForce + dampingForce) / mass;
      velocity += acceleration;
      
      // Update position
      position += velocity;

      // Update the gauge
      setAnimatedValue(position);
      prevValueRef.current = position;

      // Stop conditions
      const isSettled = Math.abs(displacement) < 0.0001 && Math.abs(velocity) < 0.0001;
      
      if (!isSettled) {
        animationRef.current = requestAnimationFrame(animate);
      } else {
        // Ensure we end exactly at the target
        setAnimatedValue(targetValue);
        prevValueRef.current = targetValue;
        velocityRef.current = 0;
      }
    };

    // Start animation
    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [normalizedValue]);

  return (
    <Box sx={containerStyle}>
      <GaugeChart
        {...chartProps}
        percent={animatedValue}
        formatTextValue={() => formatValue(value)}
      />
    </Box>
  );
});

export default AnimatedGauge; 