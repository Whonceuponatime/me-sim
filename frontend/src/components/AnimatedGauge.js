import React, { useState, useRef, useEffect, memo } from 'react';
import { Box, Typography } from '@mui/material';
import GaugeChart from 'react-gauge-chart';

const AnimatedGauge = memo(({ id, value, normalizedValue, label, formatValue, colors }) => {
  const [animatedValue, setAnimatedValue] = useState(0);
  const prevValueRef = useRef(normalizedValue);
  const animationFrameRef = useRef();

  useEffect(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    const startValue = prevValueRef.current;
    const endValue = normalizedValue;
    const duration = 1000;
    const startTime = performance.now();

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      const easeProgress = progress < 0.5
        ? 4 * progress * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 3) / 2;

      const currentValue = startValue + (endValue - startValue) * easeProgress;
      setAnimatedValue(currentValue);

      if (progress < 1) {
        animationFrameRef.current = requestAnimationFrame(animate);
      } else {
        prevValueRef.current = endValue;
      }
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [normalizedValue]);

  return (
    <Box sx={{ 
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <Box sx={{ 
        width: '100%',
        height: '200px',
        position: 'relative',
        '& > div': {
          position: 'absolute !important',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '100% !important',
          height: '100% !important',
        }
      }}>
        <GaugeChart
          id={id}
          nrOfLevels={20}
          percent={animatedValue}
          colors={colors}
          arcWidth={0.3}
          textColor="#000000"
          formatTextValue={() => formatValue(value)}
          cornerRadius={3}
          marginInPercent={0.02}
          animate={false}
        />
      </Box>
    </Box>
  );
});

export default AnimatedGauge; 