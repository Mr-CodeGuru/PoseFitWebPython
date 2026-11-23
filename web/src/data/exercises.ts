export interface ExerciseDefinition {
  id: string;
  name: string;
  type: 'repetition' | 'duration';
  bilateral: boolean;
  targetMuscles: string[];
  equipment: string;
  difficulty: 'beginner' | 'intermediate';
  description: string;
  defaultReps: number;
  targetDuration: number | null;
}

export const EXERCISE_CATALOG: ExerciseDefinition[] = [
  {
    "id": "bicep_curl",
    "name": "Bicep Curl",
    "type": "repetition",
    "bilateral": true,
    "targetMuscles": [
      "Biceps",
      "Brachialis"
    ],
    "equipment": "Dumbbells",
    "difficulty": "beginner",
    "description": "Classic bicep curl with controlled tempo",
    "defaultReps": 10,
    "targetDuration": null
  },
  {
    "id": "calf_raise",
    "name": "Calf Raise",
    "type": "repetition",
    "bilateral": false,
    "targetMuscles": [
      "Calves",
      "Soleus"
    ],
    "equipment": "Bodyweight",
    "difficulty": "beginner",
    "description": "Standing calf raises for lower leg strength",
    "defaultReps": 15,
    "targetDuration": null
  },
  {
    "id": "deadlift",
    "name": "Deadlift",
    "type": "repetition",
    "bilateral": false,
    "targetMuscles": [
      "Hamstrings",
      "Glutes",
      "Lower Back"
    ],
    "equipment": "Bodyweight or Barbell",
    "difficulty": "intermediate",
    "description": "Hip hinge movement for posterior chain strength",
    "defaultReps": 8,
    "targetDuration": null
  },
  {
    "id": "glute_bridge",
    "name": "Glute Bridge",
    "type": "repetition",
    "bilateral": false,
    "targetMuscles": [
      "Glutes",
      "Hamstrings",
      "Core"
    ],
    "equipment": "Bodyweight",
    "difficulty": "beginner",
    "description": "Hip bridge for glute activation and hip extension",
    "defaultReps": 12,
    "targetDuration": null
  },
  {
    "id": "hammer_curl",
    "name": "Hammer Curl",
    "type": "repetition",
    "bilateral": true,
    "targetMuscles": [
      "Biceps",
      "Brachialis",
      "Forearms"
    ],
    "equipment": "Dumbbells",
    "difficulty": "beginner",
    "description": "Dumbbell hammer curl for bicep development",
    "defaultReps": 8,
    "targetDuration": null
  },
  {
    "id": "high_knees",
    "name": "High Knees",
    "type": "repetition",
    "bilateral": true,
    "targetMuscles": [
      "Hip Flexors",
      "Quads",
      "Core"
    ],
    "equipment": "Bodyweight",
    "difficulty": "beginner",
    "description": "Running in place with high knee lifts",
    "defaultReps": 20,
    "targetDuration": null
  },
  {
    "id": "jumping_jack",
    "name": "Jumping Jack",
    "type": "repetition",
    "bilateral": false,
    "targetMuscles": [
      "Full Body",
      "Shoulders",
      "Legs"
    ],
    "equipment": "Bodyweight",
    "difficulty": "beginner",
    "description": "Classic full body cardio movement",
    "defaultReps": 20,
    "targetDuration": null
  },
  {
    "id": "lateral_raise",
    "name": "Lateral Raise",
    "type": "repetition",
    "bilateral": false,
    "targetMuscles": [
      "Shoulders (Lateral Deltoid)",
      "Upper Trapezius"
    ],
    "equipment": "Dumbbells",
    "difficulty": "beginner",
    "description": "Side raise for shoulder development",
    "defaultReps": 12,
    "targetDuration": null
  },
  {
    "id": "leg_raise",
    "name": "Leg Raise",
    "type": "repetition",
    "bilateral": false,
    "targetMuscles": [
      "Lower Abs",
      "Hip Flexors"
    ],
    "equipment": "Bodyweight",
    "difficulty": "intermediate",
    "description": "Lying leg raises for lower abdominal strength",
    "defaultReps": 12,
    "targetDuration": null
  },
  {
    "id": "lunge",
    "name": "Lunge",
    "type": "repetition",
    "bilateral": false,
    "targetMuscles": [
      "Quadriceps",
      "Gluteus",
      "Hamstrings",
      "Calves"
    ],
    "equipment": "Bodyweight",
    "difficulty": "beginner",
    "description": "Forward lunge for leg strength and balance",
    "defaultReps": 10,
    "targetDuration": null
  },
  {
    "id": "mountain_climber",
    "name": "Mountain Climber",
    "type": "repetition",
    "bilateral": true,
    "targetMuscles": [
      "Core",
      "Hip Flexors",
      "Shoulders"
    ],
    "equipment": "Bodyweight",
    "difficulty": "intermediate",
    "description": "Dynamic cardio with alternating knee drives",
    "defaultReps": 20,
    "targetDuration": null
  },
  {
    "id": "plank",
    "name": "Plank",
    "type": "duration",
    "bilateral": false,
    "targetMuscles": [
      "Core",
      "Shoulders",
      "Back"
    ],
    "equipment": "Bodyweight",
    "difficulty": "beginner",
    "description": "Isometric plank hold for core strength",
    "defaultReps": 3,
    "targetDuration": 30
  },
  {
    "id": "push_up",
    "name": "Push Up",
    "type": "repetition",
    "bilateral": false,
    "targetMuscles": [
      "Chest",
      "Triceps",
      "Shoulders",
      "Core"
    ],
    "equipment": "Bodyweight",
    "difficulty": "beginner",
    "description": "Classic push-up exercise for upper body strength",
    "defaultReps": 10,
    "targetDuration": null
  },
  {
    "id": "shoulder_press",
    "name": "Shoulder Press",
    "type": "repetition",
    "bilateral": false,
    "targetMuscles": [
      "Shoulders",
      "Triceps",
      "Upper Back"
    ],
    "equipment": "Dumbbells or Barbell",
    "difficulty": "beginner",
    "description": "Overhead press for shoulder development",
    "defaultReps": 10,
    "targetDuration": null
  },
  {
    "id": "side_lunge",
    "name": "Side Lunge",
    "type": "repetition",
    "bilateral": false,
    "targetMuscles": [
      "Quadriceps",
      "Gluteus",
      "Adductors",
      "Hip Flexors"
    ],
    "equipment": "Bodyweight",
    "difficulty": "beginner",
    "description": "Lateral lunge for inner thigh and hip mobility",
    "defaultReps": 10,
    "targetDuration": null
  },
  {
    "id": "squat",
    "name": "Squat",
    "type": "repetition",
    "bilateral": false,
    "targetMuscles": [
      "Quadriceps",
      "Gluteus",
      "Hamstrings"
    ],
    "equipment": "Bodyweight or Barbell",
    "difficulty": "beginner",
    "description": "Basic squat exercise targeting lower body muscles",
    "defaultReps": 10,
    "targetDuration": null
  },
  {
    "id": "tricep_dip",
    "name": "Tricep Dip",
    "type": "repetition",
    "bilateral": false,
    "targetMuscles": [
      "Triceps",
      "Shoulders",
      "Chest"
    ],
    "equipment": "Chair or Bench",
    "difficulty": "intermediate",
    "description": "Chair or bench dips for tricep strength",
    "defaultReps": 10,
    "targetDuration": null
  },
  {
    "id": "wall_sit",
    "name": "Wall Sit",
    "type": "duration",
    "bilateral": false,
    "targetMuscles": [
      "Quadriceps",
      "Glutes"
    ],
    "equipment": "Wall",
    "difficulty": "beginner",
    "description": "Isometric hold against wall for quad endurance",
    "defaultReps": 3,
    "targetDuration": 30
  }
];

export const EXERCISE_MAP: Record<string, ExerciseDefinition> = Object.fromEntries(
  EXERCISE_CATALOG.map((ex) => [ex.id, ex])
);
