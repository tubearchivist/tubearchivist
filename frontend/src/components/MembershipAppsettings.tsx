import { useEffect, useState } from 'react';
import APIClient, { ApiError } from '../functions/APIClient';
import LoadingIndicator from './LoadingIndicator';

type ApiTokenResponse = {
  token: string;
};

type ProfileUserType = {
  id: number;
  username: string;
};

type SponsorTierType = {
  tier_id: number;
  name: string;
  description: string;
  max_subs: number;
};

type ProfileResponseType = {
  id: number;
  user: ProfileUserType;
  sponsor_tier: SponsorTierType;
  subscription_count: number;
  subscription_is_max: boolean;
};

export default function MembershipAppsettings({ show_help_text }: { show_help_text: boolean }) {
  const [inputType, setInputType] = useState('password');
  const [membershipApiToken, setMembershipApiToken] = useState<string | null>(null);
  const [newToken, setNewToken] = useState<string | null>(null);
  const [profileResponse, setProfileResponse] = useState<ProfileResponseType | null>(null);
  const [profileResponseError, setProfileResponseError] = useState('');
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isLoadingSync, setIsLoadingSync] = useState(false);
  const [subSyncMessage, setSubSyncMessage] = useState('');

  const fetchMembershipToken = async () => {
    const apiTokenResponse = await APIClient<ApiTokenResponse>(
      '/api/appsettings/membership/token/',
    );
    setMembershipApiToken(apiTokenResponse.data?.token || null);
  };

  const deleteMembershipToken = async () => {
    await APIClient('/api/appsettings/membership/token/', { method: 'DELETE' });
    setMembershipApiToken(null);
    setProfileResponseError('');
    setProfileResponse(null);
  };

  const updateToken = async () => {
    const { data } = await APIClient<ApiTokenResponse>('/api/appsettings/membership/token/', {
      method: 'POST',
      body: { token: newToken },
    });
    if (data) {
      setNewToken(null);
      setMembershipApiToken(data.token);
      setInputType('password');
    }
  };

  useEffect(() => {
    fetchMembershipToken();
  }, []);

  const fetchProfile = async () => {
    setProfileResponse(null);
    setProfileResponseError('');
    setSubSyncMessage('');

    try {
      setIsLoadingProfile(true);
      const { data } = await APIClient<ProfileResponseType>('/api/appsettings/membership/profile/');
      if (data) setProfileResponse(data);
    } catch (error) {
      const apiError = error as ApiError;
      if (apiError.status && apiError.message) {
        setProfileResponseError(apiError.message);
      }
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const fetchSyncSubscriptions = async () => {
    setProfileResponseError('');
    setSubSyncMessage('');

    try {
      setIsLoadingSync(true);
      await APIClient('/api/appsettings/membership/sync/', { method: 'POST' });
      setSubSyncMessage('Task created');
    } catch (error) {
      const apiError = error as ApiError;
      if (apiError.status && apiError.message) {
        setProfileResponseError(apiError.message);
      }
    } finally {
      setIsLoadingSync(false);
    }
  };

  const toggleShowKey = () => {
    if (inputType === 'password') {
      setInputType('text');
    } else {
      setInputType('password');
    }
  };

  const handleInputChange = (value: string) => {
    setNewToken(value);
  };

  return (
    <>
      <h2>Membership</h2>
      {show_help_text && (
        <div className="help-text">
          <p>
            Unlock additional perks by sponsoring this project. More details on{' '}
            <a href="https://members.tubearchivist.com/" target="_blank" rel="noopener noreferrer">
              members.tubearchivist.com
            </a>
            .
          </p>
          <ul>
            <li>
              Enter the API token from{' '}
              <a href="https://members.tubearchivist.com/profile">
                members.tubearchivist.com/profile
              </a>
              .
            </li>
            <li>Click on validate to verify everything is working.</li>
            <li>
              If you are subscribed to less channels than your sponsor tier allows, you can directly
              sync all your subscriptions here.
            </li>
            <ul>
              <li>Repeat the sync after changing subscriptions here.</li>
              <li>
                That will unsubscribe from channels on the membership platform if you are no longer
                subscribed here.
              </li>
            </ul>
          </ul>
        </div>
      )}
      <div className="settings-box-wrapper">
        <div>
          <p>Membership API key</p>
        </div>
        <div>
          <input
            type={inputType}
            value={newToken || membershipApiToken || ''}
            onChange={e => handleInputChange(e.target.value)}
          />
          <div className="button-box">
            {(membershipApiToken || newToken) && (
              <button onClick={toggleShowKey}>{inputType === 'password' ? 'Show' : 'Hide'}</button>
            )}
            {newToken && (
              <>
                <button onClick={updateToken}>Save</button>
                <button onClick={() => setNewToken(null)}>Cancel</button>
              </>
            )}
            {membershipApiToken && (
              <button className="danger-button" onClick={deleteMembershipToken}>
                Delete
              </button>
            )}
          </div>
        </div>
        {membershipApiToken && (
          <>
            <div>
              <p>Your Profile</p>
            </div>
            <div>
              <div className="button-box">
                {isLoadingProfile ? (
                  <LoadingIndicator />
                ) : (
                  <button onClick={fetchProfile}>Validate</button>
                )}
                {isLoadingSync ? (
                  <LoadingIndicator />
                ) : (
                  <button onClick={fetchSyncSubscriptions}>Sync Subscriptions</button>
                )}
              </div>
              {profileResponseError && <p className="danger-zone">Error: {profileResponseError}</p>}
              {profileResponse && (
                <>
                  <p>
                    Username: {profileResponse.user.username}
                    <br />
                    Sponsortier: {profileResponse.sponsor_tier.name} -{' '}
                    {profileResponse.sponsor_tier.description}
                    <br />
                    Subscriptions: {profileResponse.subscription_count}/
                    {profileResponse.sponsor_tier.max_subs}
                  </p>
                </>
              )}
              {subSyncMessage && <p>Sync: {subSyncMessage}</p>}
            </div>
          </>
        )}
      </div>
    </>
  );
}
