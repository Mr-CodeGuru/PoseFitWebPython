import React, { useState } from 'react';
import {
  Dumbbell,
  Timer,
  ArrowLeftRight,
  Flame,
} from 'lucide-react';

export type ExerciseCategory = 'all' | 'arms' | 'legs' | 'core' | 'full_body';

export interface ExerciseMetadata {
  id: string;
  name: string;
  category: ExerciseCategory;
  type: 'repetition' | 'duration';
  bilateral: boolean;
  targetMuscles: string[];
  equipment: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  description: string;
}

export const EXERCISE_DATABASE: Record<string, ExerciseMetadata> = {
  squat: {
    id: 'squat',
    name: 'Squat',
    category: 'legs',
    type: 'repetition',
    bilateral: false,
    targetMuscles: ['Quadriceps', 'Glutes', 'Hamstrings'],
    equipment: 'Bodyweight',
    difficulty: 'beginner',
    description: 'Fundamental lower body strength movement targeting quads & glutes.',
  },
  push_up: {
    id: 'push_up',
    name: 'Push Up',
    category: 'arms',
    type: 'repetition',
    bilateral: false,
    targetMuscles: ['Chest', 'Triceps', 'Deltoids'],
    equipment: 'Bodyweight',
    difficulty: 'beginner',
    description: 'Classic upper body horizontal push building chest and core stability.',
  },
  plank: {
    id: 'plank',
    name: 'Plank',
    category: 'core',
    type: 'duration',
    bilateral: false,
    targetMuscles: ['Core', 'Shoulders', 'Lower Back'],
    equipment: 'Bodyweight',
    difficulty: 'beginner',
    description: 'Isometric core stability hold maintaining complete spinal alignment.',
  },
  bicep_curl: {
    id: 'bicep_curl',
    name: 'Bicep Curl',
    category: 'arms',
    type: 'repetition',
    bilateral: true,
    targetMuscles: ['Biceps', 'Brachialis'],
    equipment: 'Dumbbells',
    difficulty: 'beginner',
    description: 'Isolated arm curling movement with independent bilateral tracking.',
  },
  hammer_curl: {
    id: 'hammer_curl',
    name: 'Hammer Curl',
    category: 'arms',
    type: 'repetition',
    bilateral: true,
    targetMuscles: ['Brachioradialis', 'Biceps', 'Forearms'],
    equipment: 'Dumbbells',
    difficulty: 'beginner',
    description: 'Neutral grip arm curl building forearm thickness and bicep peaks.',
  },
  lunge: {
    id: 'lunge',
    name: 'Lunge',
    category: 'legs',
    type: 'repetition',
    bilateral: false,
    targetMuscles: ['Quads', 'Hamstrings', 'Glutes'],
    equipment: 'Bodyweight',
    difficulty: 'beginner',
    description: 'Unilateral leg split squat improving hip mobility and single-leg balance.',
  },
  side_lunge: {
    id: 'side_lunge',
    name: 'Side Lunge',
    category: 'legs',
    type: 'repetition',
    bilateral: false,
    targetMuscles: ['Adductors', 'Quads', 'Glutes'],
    equipment: 'Bodyweight',
    difficulty: 'beginner',
    description: 'Lateral frontal plane lunge targeting inner thighs and hips.',
  },
  deadlift: {
    id: 'deadlift',
    name: 'Deadlift',
    category: 'legs',
    type: 'repetition',
    bilateral: false,
    targetMuscles: ['Hamstrings', 'Glutes', 'Spinal Erectors'],
    equipment: 'Barbell or Dumbbells',
    difficulty: 'intermediate',
    description: 'Posterior chain hinge movement with strict flat-back posture.',
  },
  glute_bridge: {
    id: 'glute_bridge',
    name: 'Glute Bridge',
    category: 'legs',
    type: 'repetition',
    bilateral: false,
    targetMuscles: ['Glutes', 'Hamstrings', 'Core'],
    equipment: 'Bodyweight',
    difficulty: 'beginner',
    description: 'Floor hip thrust for glute activation and lumbar-pelvic stabilization.',
  },
  calf_raise: {
    id: 'calf_raise',
    name: 'Calf Raise',
    category: 'legs',
    type: 'repetition',
    bilateral: false,
    targetMuscles: ['Gastrocnemius', 'Soleus'],
    equipment: 'Bodyweight',
    difficulty: 'beginner',
    description: 'Ankle plantarflexion elevation for strong and explosive lower calves.',
  },
  jumping_jack: {
    id: 'jumping_jack',
    name: 'Jumping Jack',
    category: 'full_body',
    type: 'repetition',
    bilateral: false,
    targetMuscles: ['Full Body', 'Cardio', 'Shoulders'],
    equipment: 'Bodyweight',
    difficulty: 'beginner',
    description: 'Dynamic aerobic jump tracking overhead arm extension and leg spread.',
  },
  lateral_raise: {
    id: 'lateral_raise',
    name: 'Lateral Raise',
    category: 'arms',
    type: 'repetition',
    bilateral: false,
    targetMuscles: ['Lateral Deltoids', 'Trapezius'],
    equipment: 'Dumbbells',
    difficulty: 'beginner',
    description: 'Side arm elevation targeting side shoulder width without torso sway.',
  },
  shoulder_press: {
    id: 'shoulder_press',
    name: 'Shoulder Press',
    category: 'arms',
    type: 'repetition',
    bilateral: false,
    targetMuscles: ['Anterior Deltoids', 'Triceps', 'Upper Chest'],
    equipment: 'Dumbbells or Barbell',
    difficulty: 'beginner',
    description: 'Vertical overhead press requiring strict core brace and arm symmetry.',
  },
  tricep_dip: {
    id: 'tricep_dip',
    name: 'Tricep Dip',
    category: 'arms',
    type: 'repetition',
    bilateral: false,
    targetMuscles: ['Triceps', 'Anterior Deltoids', 'Chest'],
    equipment: 'Chair / Bench',
    difficulty: 'intermediate',
    description: 'Bodyweight elbow flexion lowering against bench or chair.',
  },
  wall_sit: {
    id: 'wall_sit',
    name: 'Wall Sit',
    category: 'legs',
    type: 'duration',
    bilateral: false,
    targetMuscles: ['Quadriceps', 'Glutes', 'Calves'],
    equipment: 'Wall',
    difficulty: 'beginner',
    description: '90-degree isometric quad burn against wall for leg endurance.',
  },
  high_knees: {
    id: 'high_knees',
    name: 'High Knees',
    category: 'full_body',
    type: 'repetition',
    bilateral: true,
    targetMuscles: ['Hip Flexors', 'Quads', 'Core'],
    equipment: 'Bodyweight',
    difficulty: 'beginner',
    description: 'High tempo in-place knee drives tracked bilaterally on both hips.',
  },
  mountain_climber: {
    id: 'mountain_climber',
    name: 'Mountain Climber',
    category: 'full_body',
    type: 'repetition',
    bilateral: true,
    targetMuscles: ['Core', 'Hip Flexors', 'Shoulders'],
    equipment: 'Bodyweight',
    difficulty: 'intermediate',
    description: 'Plank running knee tucks with independent left and right rep scoring.',
  },
  leg_raise: {
    id: 'leg_raise',
    name: 'Leg Raise',
    category: 'core',
    type: 'repetition',
    bilateral: false,
    targetMuscles: ['Lower Abdominals', 'Hip Flexors'],
    equipment: 'Bodyweight',
    difficulty: 'intermediate',
    description: 'Lying lower abdominal flexion raising legs straight to 90 degrees.',
  },
};

interface ExerciseSelectorProps {
  availableExercises: string[];
  selectedExercise: string;
  onSelectExercise: (name: string) => void;
  disabled?: boolean;
}

export const ExerciseSelector: React.FC<ExerciseSelectorProps> = ({
  availableExercises,
  selectedExercise,
  onSelectExercise,
  disabled = false,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<ExerciseCategory>('all');
  const [searchQuery] = useState('');

  const getExerciseIcon = (name: string) => {
    const meta = EXERCISE_DATABASE[name];
    if (meta?.type === 'duration') {
      return <Timer className="w-3.5 h-3.5 text-amber-400" />;
    }
    if (meta?.bilateral) {
      return <ArrowLeftRight className="w-3.5 h-3.5 text-sky-400" />;
    }
    if (meta?.category === 'full_body') {
      return <Flame className="w-3.5 h-3.5 text-rose-400" />;
    }
    return <Dumbbell className="w-3.5 h-3.5 text-emerald-400" />;
  };

  const formatExerciseName = (name: string) => {
    const meta = EXERCISE_DATABASE[name];
    if (meta) return meta.name;
    return name
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const categories: { id: ExerciseCategory; label: string }[] = [
    { id: 'all', label: 'All' },
    { id: 'legs', label: 'Legs' },
    { id: 'arms', label: 'Arms' },
    { id: 'core', label: 'Core' },
    { id: 'full_body', label: 'Full Body' },
  ];

  const filteredExercises = availableExercises.filter((name) => {
    const meta = EXERCISE_DATABASE[name];
    const matchesCategory =
      selectedCategory === 'all' || (meta && meta.category === selectedCategory);
    const matchesSearch =
      searchQuery.trim() === '' ||
      formatExerciseName(name).toLowerCase().includes(searchQuery.toLowerCase()) ||
      meta?.targetMuscles.some((m) => m.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="flex flex-col gap-2 w-full">
      {/* Category Pills & Quick Filter Bar */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
        {categories.map((cat) => (
          <button
            key={cat.id}
            type="button"
            onClick={() => setSelectedCategory(cat.id)}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold tracking-wide transition-all cursor-pointer whitespace-nowrap ${
              selectedCategory === cat.id
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm shadow-emerald-500/10'
                : 'bg-slate-900/60 text-slate-400 border border-slate-800/80 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Exercise Pill Carousel */}
      <div className="flex items-center space-x-2 overflow-x-auto py-1 px-0.5 scrollbar-thin">
        {filteredExercises.map((name) => {
          const isSelected = name === selectedExercise;
          const meta = EXERCISE_DATABASE[name];
          return (
            <button
              key={name}
              type="button"
              disabled={disabled}
              onClick={() => onSelectExercise(name)}
              className={`group flex items-center space-x-2 px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-200 border cursor-pointer ${
                isSelected
                  ? 'bg-gradient-to-r from-emerald-500/25 to-teal-500/20 text-white border-emerald-400/60 shadow-md shadow-emerald-500/20 ring-1 ring-emerald-400/40'
                  : 'bg-slate-900/80 text-slate-300 border-slate-800/90 hover:border-slate-700 hover:bg-slate-800/60 hover:text-white'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : 'active:scale-95'}`}
            >
              <div
                className={`p-1 rounded-lg ${
                  isSelected ? 'bg-emerald-500/30' : 'bg-slate-800/80 group-hover:bg-slate-700'
                }`}
              >
                {getExerciseIcon(name)}
              </div>
              <div className="flex flex-col text-left">
                <span className="leading-tight font-bold">{formatExerciseName(name)}</span>
                {meta && (
                  <span className="text-[9px] text-slate-400 font-medium group-hover:text-slate-300">
                    {meta.targetMuscles[0]}
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
