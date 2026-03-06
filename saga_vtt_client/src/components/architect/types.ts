export type TabType = 'GEOGRAPHY' | 'BIOMES' | 'RESOURCES' | 'CLIMATE' | 'ECOSYSTEM' | 'CULTURES' | 'FACTIONS' | 'RELIGIONS' | 'BUILDINGS' | 'PAINTING' | 'CHRONOS';

export interface ArchitectTab {
    id: TabType;
    label: string;
    icon: any;
    color: string;
}
