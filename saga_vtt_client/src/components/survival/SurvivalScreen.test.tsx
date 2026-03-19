import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SurvivalScreen } from './SurvivalScreen';

// Mock the store hooks
vi.mock('../../store/useGameStore', () => ({
    useGameStore: vi.fn(),
}));

vi.mock('../../store/useWorldStore', () => ({
    useWorldStore: vi.fn(),
}));

vi.mock('../../store/useCharacterStore', () => ({
    useCharacterStore: vi.fn(),
}));

import { useGameStore } from '../../store/useGameStore';
import { useWorldStore } from '../../store/useWorldStore';
import { useCharacterStore } from '../../store/useCharacterStore';

describe('SurvivalScreen Component', () => {
    // Setup mock implementations for the stores
    const mockSetVttTier = vi.fn();
    const mockAssignSurvivalJob = vi.fn();

    const mockGameStoreState = {
        setVttTier: mockSetVttTier,
        survivalJobs: [],
        assignSurvivalJob: mockAssignSurvivalJob,
        rations: 5,
        fuel: 3,
    };

    const mockWorldStoreState = {
        selectedHex: {
            biome_tag: 'FOREST',
            elevation: 0.5,
        },
    };

    const mockCharacterStoreState = {
        characterName: 'Thorin',
    };

    beforeEach(() => {
        vi.clearAllMocks();

        // Implement the selector behavior for mocked stores
        (useGameStore as any).mockImplementation((selector: any) => selector(mockGameStoreState));
        (useWorldStore as any).mockImplementation((selector: any) => selector(mockWorldStoreState));
        (useCharacterStore as any).mockImplementation((selector: any) => selector(mockCharacterStoreState));
    });

    it('renders basic character and resource information correctly', () => {
        render(<SurvivalScreen />);

        // Character name
        expect(screen.getByText('Thorin')).toBeInTheDocument();

        // Rations
        expect(screen.getByText('5')).toBeInTheDocument();
        expect(screen.getByText('Rations')).toBeInTheDocument();

        // Fuel
        expect(screen.getByText('3')).toBeInTheDocument();
        expect(screen.getByText('Fuel')).toBeInTheDocument();
    });

    it('renders biome information correctly', () => {
        render(<SurvivalScreen />);

        // Biome description should be formatted
        expect(screen.getByText(/The sun dips below the horizon in the FOREST/)).toBeInTheDocument();
    });

    it('displays mountain background for high elevation or deep tundra', () => {
        const { unmount } = render(<SurvivalScreen />);

        // Default forest background

        // The background image is on the first child div
        const bgDiv = document.querySelector('.bg-cover') as HTMLElement;
        expect(bgDiv.style.backgroundImage).toContain('forest_bg.png');

        unmount();

        // Test mountain background due to elevation
        (useWorldStore as any).mockImplementation((selector: any) => selector({
            selectedHex: { biome_tag: 'FOREST', elevation: 0.9 },
        }));

        render(<SurvivalScreen />);
        const bgDivHighEl = document.querySelector('.bg-cover') as HTMLElement;
        expect(bgDivHighEl.style.backgroundImage).toContain('mountain_bg.png');

        unmount();

        // Test mountain background due to DEEP_TUNDRA
        (useWorldStore as any).mockImplementation((selector: any) => selector({
            selectedHex: { biome_tag: 'DEEP_TUNDRA', elevation: 0.5 },
        }));

        render(<SurvivalScreen />);
        const bgDivTundra = document.querySelector('.bg-cover') as HTMLElement;
        expect(bgDivTundra.style.backgroundImage).toContain('mountain_bg.png');
    });

    it('renders all survival job buttons', () => {
        render(<SurvivalScreen />);

        const jobs = ['FORAGE', 'GUARD', 'FIRE', 'REST', 'REPAIR'];
        jobs.forEach(job => {
            expect(screen.getByRole('button', { name: job })).toBeInTheDocument();
        });
    });

    it('calls assignSurvivalJob when a job button is clicked', () => {
        render(<SurvivalScreen />);

        const forageButton = screen.getByRole('button', { name: 'FORAGE' });
        fireEvent.click(forageButton);

        expect(mockAssignSurvivalJob).toHaveBeenCalledTimes(1);
        expect(mockAssignSurvivalJob).toHaveBeenCalledWith('Thorin', 'FORAGE');
    });

    it('highlights active jobs for the character', () => {
        // Mock a state where 'GUARD' is assigned to 'Thorin'
        (useGameStore as any).mockImplementation((selector: any) => selector({
            ...mockGameStoreState,
            survivalJobs: [{ characterName: 'Thorin', jobName: 'GUARD' }],
        }));

        render(<SurvivalScreen />);

        const guardButton = screen.getByRole('button', { name: 'GUARD' });
        expect(guardButton).toHaveClass('bg-amber-500'); // active class

        const forageButton = screen.getByRole('button', { name: 'FORAGE' });
        expect(forageButton).toHaveClass('bg-zinc-900'); // inactive class
    });

    it('calls setVttTier(2) when Abandon Camp is clicked', () => {
        render(<SurvivalScreen />);

        const abandonButton = screen.getByRole('button', { name: /Abandon Camp/i });
        fireEvent.click(abandonButton);

        expect(mockSetVttTier).toHaveBeenCalledTimes(1);
        expect(mockSetVttTier).toHaveBeenCalledWith(2);
    });
});
