import React, { useState, useRef, useEffect, memo } from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
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
    <Card sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      minHeight: '250px',
      position: 'relative'
    }}>
      <CardContent sx={{ 
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        padding: '16px !important'
      }}>
        <Typography 
          color="textSecondary" 
          gutterBottom
          sx={{ mb: 1 }}
        >
          {label}
        </Typography>
        <Box sx={{ 
          flex: 1,
          position: 'relative',
          '& > div': {
            position: 'absolute !important',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
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
      </CardContent>
    </Card>
  );
});

export default AnimatedGauge; 