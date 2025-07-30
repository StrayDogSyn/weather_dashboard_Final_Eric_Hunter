"""Chart Animation Mixin for Temperature Chart Component.

This module provides the ChartAnimationMixin class that handles smooth transitions,
animations, and visual effects for the temperature chart.
"""

import numpy as np
from typing import List, Callable, Optional
import threading
import time


class ChartAnimationMixin:
    """Mixin for chart animations and smooth transitions."""
    
    def __init__(self):
        """Initialize animation properties."""
        self.animation_duration = 0.8  # seconds
        self.animation_fps = 30
        self.is_animating = False
        self.animation_thread = None
        
    def animate_timeframe_transition(self, old_data: dict, new_data: dict, callback: Optional[Callable] = None):
        """Animate transition between different timeframes with enhanced effects."""
        if self.is_animating:
            return
            
        self.is_animating = True
        
        # Enhanced animation with fade effect
        self._start_fade_out_animation()
        
        # Start animation in separate thread
        self.animation_thread = threading.Thread(
            target=self._run_enhanced_timeframe_animation,
            args=(old_data, new_data, callback)
        )
        self.animation_thread.daemon = True
        self.animation_thread.start()
        
    def _run_enhanced_timeframe_animation(self, old_data: dict, new_data: dict, callback: Optional[Callable] = None):
        """Run enhanced timeframe transition animation with glassmorphic effects."""
        try:
            # Enhanced animation parameters
            total_frames = int(self.animation_duration * self.animation_fps)
            frame_delay = 1.0 / self.animation_fps
            
            # Phase 1: Fade out current data (25% of animation)
            fade_out_frames = int(total_frames * 0.25)
            for frame in range(fade_out_frames):
                if not self.is_animating:
                    break
                    
                progress = frame / fade_out_frames
                alpha = 1.0 - self._ease_in_cubic(progress)
                
                self.after_idle(self._schedule_chart_alpha_update, old_data, alpha)
                time.sleep(frame_delay)
            
            # Phase 2: Transform data (50% of animation)
            transform_frames = int(total_frames * 0.5)
            for frame in range(transform_frames):
                if not self.is_animating:
                    break
                    
                progress = frame / transform_frames
                eased_progress = self._ease_in_out_cubic(progress)
                
                interpolated_data = self._interpolate_data(old_data, new_data, eased_progress)
                self.after_idle(self._schedule_chart_frame_update, interpolated_data)
                time.sleep(frame_delay)
            
            # Phase 3: Fade in new data (25% of animation)
            fade_in_frames = int(total_frames * 0.25)
            for frame in range(fade_in_frames):
                if not self.is_animating:
                    break
                    
                progress = frame / fade_in_frames
                alpha = self._ease_out_cubic(progress)
                
                self.after_idle(self._schedule_chart_alpha_update, new_data, alpha)
                time.sleep(frame_delay)
            
            # Finalize animation
            self.after_idle(self._finalize_enhanced_animation)
            self.is_animating = False
            
            # Execute callback if provided
            if callback:
                self.after_idle(callback)
                
        except Exception as e:
            self.is_animating = False
            print(f"Enhanced animation error: {e}")
            
    def animate_data_update(self, new_temperatures: List[float], new_dates: List, callback: Optional[Callable] = None):
        """Animate chart update with new data."""
        if self.is_animating:
            return
            
        # Store current data
        old_temperatures = getattr(self, 'temperatures', [])
        old_dates = getattr(self, 'dates', [])
        
        if not old_temperatures:
            # No animation needed for first load
            self.temperatures = new_temperatures
            self.dates = new_dates
            if callback:
                callback()
            return
            
        self.is_animating = True
        
        # Start animation
        self.animation_thread = threading.Thread(
            target=self._run_data_animation,
            args=(old_temperatures, old_dates, new_temperatures, new_dates, callback)
        )
        self.animation_thread.daemon = True
        self.animation_thread.start()
        
    def _run_data_animation(self, old_temps: List[float], old_dates: List, 
                           new_temps: List[float], new_dates: List, callback: Optional[Callable] = None):
        """Run the data update animation."""
        try:
            total_frames = int(self.animation_duration * self.animation_fps)
            frame_delay = 1.0 / self.animation_fps
            
            for frame in range(total_frames + 1):
                progress = frame / total_frames
                eased_progress = self._ease_in_out_cubic(progress)
                
                # Interpolate temperature values
                interpolated_temps = self._interpolate_temperatures(old_temps, new_temps, eased_progress)
                
                # Update chart
                self.after_idle(self._schedule_temperature_update, interpolated_temps, new_dates)
                
                if frame < total_frames:
                    time.sleep(frame_delay)
                    
            # Update final data
            self.temperatures = new_temps
            self.dates = new_dates
            self.is_animating = False
            
            if callback:
                self.after_idle(callback)
                
        except Exception as e:
            self.is_animating = False
            print(f"Data animation error: {e}")
            
    def animate_chart_entrance(self, callback: Optional[Callable] = None):
        """Animate chart entrance effect."""
        if self.is_animating:
            return
            
        self.is_animating = True
        
        # Start entrance animation
        self.animation_thread = threading.Thread(
            target=self._run_entrance_animation,
            args=(callback,)
        )
        self.animation_thread.daemon = True
        self.animation_thread.start()
        
    def _run_entrance_animation(self, callback: Optional[Callable] = None):
        """Run the chart entrance animation."""
        try:
            total_frames = int(self.animation_duration * self.animation_fps)
            frame_delay = 1.0 / self.animation_fps
            
            for frame in range(total_frames + 1):
                progress = frame / total_frames
                eased_progress = self._ease_out_bounce(progress)
                
                # Scale effect
                scale = eased_progress
                alpha = eased_progress
                
                # Update chart appearance
                self.after_idle(self._schedule_chart_scale_update, scale, alpha)
                
                if frame < total_frames:
                    time.sleep(frame_delay)
                    
            self.is_animating = False
            
            if callback:
                self.after_idle(callback)
                
        except Exception as e:
            self.is_animating = False
            print(f"Entrance animation error: {e}")
            
    def _ease_in_out_cubic(self, t: float) -> float:
        """Cubic easing function for smooth animations."""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def _ease_in_cubic(self, t: float) -> float:
        """Cubic ease-in function."""
        return t * t * t
    
    def _ease_out_cubic(self, t: float) -> float:
        """Cubic ease-out function."""
        return 1 - pow(1 - t, 3)
    
    def _start_fade_out_animation(self):
        """Start fade-out effect for current chart."""
        try:
            # Add fade-out effect to current chart elements
            if hasattr(self, 'ax'):
                for line in self.ax.lines:
                    line.set_alpha(line.get_alpha() * 0.7)
                
                # Refresh canvas
                if hasattr(self, 'canvas'):
                    self.canvas.draw_idle()
                    
        except Exception as e:
            print(f"Fade-out animation error: {e}")
    
    def _update_chart_alpha(self, data: dict, alpha: float):
        """Update chart elements alpha for fade effects."""
        try:
            if hasattr(self, 'ax'):
                # Update line alpha
                for line in self.ax.lines:
                    line.set_alpha(alpha)
                
                # Update fill alpha
                for collection in self.ax.collections:
                    collection.set_alpha(alpha * 0.3)
                
                # Refresh canvas
                if hasattr(self, 'canvas'):
                    self.canvas.draw_idle()
                    
        except Exception as e:
            print(f"Alpha update error: {e}")
    
    def _finalize_enhanced_animation(self):
        """Finalize enhanced animation with glassmorphic effects."""
        try:
            if hasattr(self, 'ax'):
                # Restore full opacity
                for line in self.ax.lines:
                    line.set_alpha(1.0)
                
                # Apply final glassmorphic styling
                if hasattr(self, 'apply_glassmorphic_styling'):
                    self.apply_glassmorphic_styling()
                
                # Final canvas refresh
                if hasattr(self, 'canvas'):
                    self.canvas.draw()
                    
        except Exception as e:
            print(f"Animation finalization error: {e}")
            
    def _ease_out_bounce(self, t: float) -> float:
        """Bounce easing function for entrance effects."""
        n1 = 7.5625
        d1 = 2.75
        
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375
            
    def _interpolate_data(self, old_data: dict, new_data: dict, progress: float) -> dict:
        """Interpolate between old and new data sets."""
        interpolated = {}
        
        # Interpolate temperatures
        if 'temperatures' in old_data and 'temperatures' in new_data:
            interpolated['temperatures'] = self._interpolate_temperatures(
                old_data['temperatures'], new_data['temperatures'], progress
            )
            
        # Use new dates (no interpolation needed)
        if 'dates' in new_data:
            interpolated['dates'] = new_data['dates']
            
        return interpolated
        
    def _interpolate_temperatures(self, old_temps: List[float], new_temps: List[float], progress: float) -> List[float]:
        """Interpolate between old and new temperature values."""
        if len(old_temps) != len(new_temps):
            # Different lengths - use new data
            return new_temps
            
        interpolated = []
        for old_temp, new_temp in zip(old_temps, new_temps):
            interpolated_temp = old_temp + (new_temp - old_temp) * progress
            interpolated.append(interpolated_temp)
            
        return interpolated
        
    def _update_chart_frame(self, data: dict):
        """Update chart with interpolated data frame."""
        if 'temperatures' in data and 'dates' in data:
            self._update_temperature_line(data['temperatures'], data['dates'])
            
    def _update_temperature_line(self, temperatures: List[float], dates: List):
        """Update the temperature line with new data."""
        # Clear existing lines
        for line in self.ax.lines:
            line.remove()
            
        # Plot new line
        if temperatures and dates:
            self.ax.plot(
                dates, temperatures,
                color='#00ff88',
                linewidth=2,
                marker='o',
                markersize=4,
                alpha=0.8
            )
            
        # Refresh display
        self.canvas.draw_idle()
        
    def _update_chart_scale(self, scale: float, alpha: float):
        """Update chart scale and transparency for entrance animation."""
        # Apply scale transformation
        self.ax.set_xlim(
            self.ax.get_xlim()[0] * scale,
            self.ax.get_xlim()[1] * scale
        )
        
        # Apply alpha to all chart elements
        for line in self.ax.lines:
            line.set_alpha(alpha)
            
        for text in self.ax.texts:
            text.set_alpha(alpha)
            
        # Refresh display
        self.canvas.draw_idle()
        
    def pulse_animation(self, element_type: str = "line", duration: float = 1.0):
        """Create a pulse animation effect on chart elements."""
        if self.is_animating:
            return
            
        self.is_animating = True
        
        # Start pulse animation
        self.animation_thread = threading.Thread(
            target=self._run_pulse_animation,
            args=(element_type, duration)
        )
        self.animation_thread.daemon = True
        self.animation_thread.start()
        
    def _run_pulse_animation(self, element_type: str, duration: float):
        """Run pulse animation effect."""
        try:
            total_frames = int(duration * self.animation_fps)
            frame_delay = 1.0 / self.animation_fps
            
            for frame in range(total_frames + 1):
                progress = frame / total_frames
                
                # Create pulse effect (sine wave)
                pulse_value = 0.5 + 0.5 * np.sin(progress * 4 * np.pi)
                
                # Apply pulse to elements
                if element_type == "line":
                    self.after_idle(self._schedule_line_pulse, pulse_value)
                elif element_type == "markers":
                    self.after_idle(self._schedule_marker_pulse, pulse_value)
                    
                if frame < total_frames:
                    time.sleep(frame_delay)
                    
            # Reset to normal
            self.after_idle(self._reset_pulse_effects)
            self.is_animating = False
            
        except Exception as e:
            self.is_animating = False
            print(f"Pulse animation error: {e}")
            
    def _apply_line_pulse(self, pulse_value: float):
        """Apply pulse effect to chart lines."""
        for line in self.ax.lines:
            line.set_alpha(0.5 + 0.5 * pulse_value)
            line.set_linewidth(2 + pulse_value * 2)
            
        self.canvas.draw_idle()
        
    def _apply_marker_pulse(self, pulse_value: float):
        """Apply pulse effect to chart markers."""
        for line in self.ax.lines:
            line.set_markersize(4 + pulse_value * 4)
            
        self.canvas.draw_idle()
        
    def _reset_pulse_effects(self):
        """Reset pulse effects to normal state."""
        for line in self.ax.lines:
            line.set_alpha(0.8)
            line.set_linewidth(2)
            line.set_markersize(4)
            
        self.canvas.draw_idle()
        
    def stop_all_animations(self):
        """Stop all running animations."""
        self.is_animating = False
        
        if self.animation_thread and self.animation_thread.is_alive():
            # Note: Cannot force stop thread, but setting flag will stop animation loop
            pass
            
    def set_animation_speed(self, speed_multiplier: float):
        """Set animation speed multiplier."""
        self.animation_duration = 0.8 / max(0.1, speed_multiplier)
        
    def is_animation_running(self) -> bool:
        """Check if any animation is currently running."""
        return self.is_animating
    
    def _schedule_chart_frame_update(self, data):
        """Helper method to schedule chart frame update."""
        self._update_chart_frame(data)
    
    def _schedule_temperature_update(self, temps, dates):
        """Helper method to schedule temperature line update."""
        self._update_temperature_line(temps, dates)
    
    def _schedule_chart_scale_update(self, scale, alpha):
        """Helper method to schedule chart scale update."""
        self._update_chart_scale(scale, alpha)
    
    def _schedule_line_pulse(self, pulse_value):
        """Helper method to schedule line pulse effect."""
        self._apply_line_pulse(pulse_value)
    
    def _schedule_marker_pulse(self, pulse_value):
        """Helper method to schedule marker pulse effect."""
        self._apply_marker_pulse(pulse_value)
    
    def _schedule_chart_alpha_update(self, data, alpha):
        """Helper method to schedule chart alpha update."""
        self._update_chart_alpha(data, alpha)