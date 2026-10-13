export interface ParkingBranch {
  id: string;
  name: string;
  city: string;
  capacity: number;
}

export const INITIAL_BRANCHES: ParkingBranch[] = [
  {
    id: "01",
    name: "Sede Principal",
    city: "Mosquera, Cundinamarca.",
    capacity: 120,
  },
];
